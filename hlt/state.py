import hlt
from hlt.positionals import Direction, Position # This library contains direction metadata to better interface with the game.
from hlt import constants

import random  # This library allows you to generate random numbers.
import logging
import numpy as np
import heapq
from itertools import product
from collections import defaultdict
import time

from scipy.ndimage.filters import gaussian_filter

class map_graph(object):

    def __init__(self, precomp):
        self.cells = [(y, x) for y,x in product(range(precomp.h), range(precomp.w))]
        self.neighbors = defaultdict(list)

        dirs = [[0,1],[0,-1],[1,0],[-1,0]]
        for cell in self.cells:
            for d in dirs:
                ncell = tuple([ (cell[0] + d[0])%precomp.h, (cell[1] + d[1])%precomp.w])
                self.neighbors[cell].append(ncell)


class Precomp(object):
    ''' Perform any useful computations prior to the game start.
        Also contains data structures that need to persist across multiple turns'''

    def __init__(self, game):
        self.game = game
        self.gmap = self.game.game_map

        # Number of players in the game (2 or 4)
        self.nplayers = len(self.game.players.keys())

        # Map width/height
        self.w = self.gmap.width
        self.h = self.gmap.height

        # Arrays containing the x and y coordinates of each cell
        self.xcoords = np.array([[x for x in range(self.w)] for y in range(self.h)], dtype='int')
        self.ycoords = np.array([[y for x in range(self.w)] for y in range(self.h)], dtype='int')

        # Array containing time coordinates for projecting halite mining up to 60 turns ahead
        self.maxt = 60
        self.tcoords = np.outer(np.linspace(1,self.maxt, self.maxt), np.ones((self.h, self.w)))
        self.tcoords = self.tcoords.reshape((self.maxt, self.h, self.w))
        self.tcoords = self.tcoords.astype(np.float32)

        # The map turned into a graph for Dijkstra and A* algorithm
        self.mapgraph = map_graph(self)

        # Halite at the beginning of the game
        self.initial_halite = np.sum(np.array([[cell.halite_amount for cell in row] \
                                         for row in self.gmap._cells], dtype='float32'),
                                     axis=(0,1))

        # Factors for concentration heuristic in cell scoring
        # Favors concentration in 4p games
        if self.nplayers == 2:
            self.concentration_fac = np.max([0, 0.4*(self.h/32. - 1.) + 0.1])
        elif self.nplayers == 4:
            self.concentration_fac = np.max([0, 0.4*(self.h/32. - 1.) + 0.5])
        
        # Maximum dropoff limit depends on the map size
        self.max_dropoffs = np.min([(self.w - 24)//8, 4])

        # Hard-coded locations for potential dropoffs
        if self.nplayers == 2:
            self.dropoff_centroids = [(self.h//4, 0), (3*self.h//4, 0), 
                                      (self.h//4, self.w//2), (3*self.h//4, self.w//2)]
        elif self.nplayers == 4:
            self.dropoff_centroids = [(0, 0), (self.h//2, 0), 
                                      (self.h//2, self.w//2), (0, self.w//2)]
        self.ghost_dropoffs = []

        # Keeps track of the nearest (self-owned) entity.Entity to each cell
        self.nearest_dropoff = np.full((self.h, self.w), self.game.me.shipyard)

class GameState(object):
    ''' Central class for controlling the game state.
        Contains data structures that renew each turn.'''

    def __init__(self, game, precomp):
        logging.info('Updating Game State')
        self.pc = precomp
        self.game = game
        self.gmap = self.game.game_map

        self.turn = self.game.turn_number # get turn number
        self.nplayers = self.pc.nplayers

        # list of enemy player object. Should be in Precomp.
        self.enemy_players = [p for p in self.game.players.values() 
                                         if p != self.game.me]
        
        # Keep track of number of ships
        self.nships = len(self.game.me.get_ships())
        self.ndrops = len(self.game.me.get_dropoffs())
        logging.info('n_ships: '+str(self.nships))
        logging.info('n_drops: '+str(self.ndrops))
        self.enemy_nships_max = 0
        self.enemy_nships_total = 0
        self.enemy_dropoffs_max = 0
        for p in self.enemy_players:
            nships = len(p.get_ships())
            self.enemy_nships_total += nships
            ndrops = len(p.get_dropoffs())
            if nships > self.enemy_nships_max:
                self.enemy_nships_max = nships
            if ndrops > self.enemy_dropoffs_max:
                self.enemy_dropoffs_max = ndrops
        self.ships_total = self.nships + self.enemy_nships_total
        logging.info('e_ships: '+str(self.enemy_nships_max))
        logging.info('e_drops: '+str(self.enemy_dropoffs_max))

        # Map things
        # Reset cell targets
        for row in self.gmap._cells:
            for cell in row:
                cell.targeted = None
                cell.enem = None

        # Keeps track of cells that have been allocated as targets
        # for mining ships to avoid duplicate assignemnts
        self.mining_targets = np.full((self.pc.h, self.pc.w), 1)
        self.mining_cell_scores = {}
        self.mining_dijk_paths = {}

        # Should be in Precomp
        self.shipyard = self.gmap[self.game.me.shipyard]

        # Various halite map manipulations
        self.halite_raw = np.array([[cell.halite_amount for cell in row] \
                                    for row in self.gmap._cells], dtype='float32')
        self.halite_conv = gaussian_filter(self.halite_raw, 1, mode='wrap', truncate=4)
        self.halite_conv_norm = self.halite_conv/np.max(self.halite_conv)
        self.halite_conv_big = gaussian_filter(self.halite_conv, 3, mode='wrap', truncate=4)
        self.halite_avg = np.mean(self.halite_raw)
        self.halite_total = np.sum(self.halite_raw, axis=(0,1))
        logging.info('Halite Remaining: '+str(self.halite_total/self.pc.initial_halite))

        # Distances and costs to the nearest dropoff for each cell
        self.dropoff_dist_arr = np.array([[self.nearest_dropoff_dist(cell)[1] 
                                           for cell in row] for row in self.gmap._cells], dtype='float32')
        self.dropoff_cost_arr = self.rev_dijk()

        # Dictionaries that store ship info to avoid redundant calculations
        self.dist_from_ship = {}
        self.mineable_halite = {}

        # Ship proximity arrays, to see where ships are aggregated.
        self.ship_proximity = {}
        self.enem_proximity = np.zeros((self.pc.h,self.pc.w), dtype='float32')
        for player in self.game.players.values():
            prox = np.zeros((self.pc.h,self.pc.w), dtype='float32')
            for ship in player.get_ships():
                pos = (ship.position.y, ship.position.x)
                for y in range(-4,5):
                    xr = 4 - abs(y)
                    for x in range(-xr, xr+1):
                        prox[(pos[0]+y)%self.pc.h, (pos[1]+x)%self.pc.w] += 1
            if player.id != self.game.me.id:
                self.enem_proximity += prox    
            self.ship_proximity[player.id] = prox
       
        # Crash arrays, to avoid crashing.
        self.crash_mask_safe = np.zeros((self.pc.h,self.pc.w), dtype='float32')
        self.crash_mask_unsafe = np.zeros((self.pc.h,self.pc.w), dtype='float32')
        for player in self.enemy_players:
            for ship in player.get_ships():
                pos = (ship.position.y, ship.position.x)
                position = Position(pos[1], pos[0])
                if not ship.prev:
                    npos = pos
                else:
                    ndir = self.gmap.get_one_move_direction(ship.prev, position)
                    nposition = position.directional_offset(ndir)
                    npos = (nposition.y, nposition.x)
                ship.prev = Position(pos[1], pos[0])

                self.crash_mask_unsafe[pos]  = 1
                self.gmap._cells[pos[0]][pos[1]].enem = ship
                self.crash_mask_unsafe[npos] = 1
                self.gmap._cells[npos[0]][npos[1]].enem = ship
                for y in range(-1,2):
                    xr = 1 - abs(y)
                    for x in range(-xr, xr+1):
                        self.crash_mask_safe[(pos[0]+y)%self.pc.h, (pos[1]+x)%self.pc.w] += 1

        # Ship things
        # Clear ship.next values
        for ship in self.game.me.get_ships(): 
            ship.next = None

        # Allocate ships to cmd queues 
        self.ships_mining  = []
        self.ships_deposit = []
        self.ships_enddepo = []
        self.ships_dropoff = []
        remaining_turns = (constants.MAX_TURNS - self.turn)
        if len(self.game.me.get_dropoffs()) < self.pc.max_dropoffs:
            self.dropoff_conditions()
        
        for ship in self.game.me.get_ships():
            # End-depositing condition
            if self.gmap.calculate_distance(ship.position, 
                                            self.shipyard.position) \
                    > remaining_turns - self.pc.w/3.:
                ship.type = "end_depositing"
            
            # Default Assignment
            if ship.type == None:
                ship.type = 'mining'

            # Update sorting metric (distance to nearest dropoff)
            # This is redundant, should draw from self.dropoff_dist_arr
            dist = 1 + self.gmap.calculate_distance(ship.position, 
                                                self.nearest_dropoff(ship).position)
            # Assign ships to their respective heaps
            if ship.type == 'mining':
                if self.convert_to_depositing(ship):
                    ship.hval = 1/dist
                    continue
                else:
                    max_score = self.get_mining_cell_est(ship)
                    if max_score == 0:
                        ship.hval = np.infty
                    else:
                        ship.hval = 1/max_score
                    heapq.heappush(self.ships_mining, ship)
            elif ship.type == 'depositing':
                # Condition to convert to mining
                ship.hval = dist
                if self.convert_to_mining(ship):
                    continue
                else:
                    heapq.heappush(self.ships_deposit, ship)
            elif ship.type == 'end_depositing':
                ship.hval = dist
                heapq.heappush(self.ships_enddepo, ship)
            elif ship.type == 'dropoff':
                ship.hval = 0
                heapq.heappush(self.ships_dropoff, ship)

        # Make sure that ghost_dropoffs don't persist beyond the death
        # of their associated ship
        if self.ships_dropoff == [] and self.pc.ghost_dropoffs != []:
            self.pc.ghost_dropoffs = []
           


    ##################################
    # Ship Type Assignment Methods
    ##################################
    def convert_to_depositing(self, ship):
        """ True if ship should change from mining to depositing,
            False else """
        if ship.halite_amount >= constants.MAX_HALITE * 0.95:
            ship.type = 'depositing'
            ship.hval = 1/ship.hval
            heapq.heappush(self.ships_deposit, ship)
            return True
        else:
            return False

    def convert_to_mining(self, ship):
        """ True if ship should change from depositing to mining,
            False else """
        if ship.halite_amount == 0:
            ship.type = 'mining'
            max_score = self.get_mining_cell_est(ship)
            if max_score == 0:
                ship.hval = np.infty
            else:
                ship.hval = 1/max_score
            heapq.heappush(self.ships_mining, ship)
            return True
        else:
            return False

    def dropoff_conditions(self):
        ''' Check to see if we should initiate the process of 
            spawning a dropoff'''
        td = time.time()

        # Conditions for exiting dropoff_conditions early
        if (self.pc.ghost_dropoffs) \ 
           or (self.turn < 70 or self.turn > constants.MAX_TURNS - 200) \
           or (self.nships < 15) \
           or (self.pc.dropoff_centroids == []):
            return

        # Score the addition of adding each dropoff
        centroid_scores = []
        for centroid in self.pc.dropoff_centroids:
            score = self.get_centroid_score(centroid)
            if score == 0:
                score = 0.0000001
            heapq.heappush(centroid_scores, (1./score, centroid))

        centroid_score, centroid = heapq.heappop(centroid_scores)
        centroid_score = 1/centroid_score

        # Score without any additional dropoffs
        current_score = 0
        for ship in self.game.me.get_ships():
            if ship.type == 'mining':
                current_score += self.get_mining_cell_est(ship)

        # If centroid score is sufficiently larger than current score,
        # build a dropoff
        if centroid_score - 2*constants.DROPOFF_COST/(constants.MAX_TURNS - self.turn + 1) > 1.*current_score:
            # find the right cell
            cPosition = Position(centroid[1], centroid[0])

            # find the closest ship to that cell and convert to dropoff type
            dheap = []
            for ship in self.game.me.get_ships():
                dist = 1 + self.gmap.calculate_distance(ship.position, 
                                                        cPosition)
                heapq.heappush(dheap, (dist, ship.id))
            dship_id = heapq.heappop(dheap)[1]
            dship = self.game.me._ships[dship_id]

            dship.type = 'dropoff'
            dship.drop = cPosition

            # remove centroid from potential dropoffs
            # and create ghost dropoff
            self.pc.dropoff_centroids.remove(centroid)
            self.pc.ghost_dropoffs.append(hlt.entity.Dropoff(self.game.me.id, 666, cPosition))

        logging.info('dropoff conditions: '+str(time.time() - td))

    ##################################
    # Map Cost Methods
    ##################################

    def nearest_dropoff(self, ship):
        ''' Find the nearest dropoff to a given entity''' 
        dropoffs = [self.game.me.shipyard]
        dropoffs.extend(self.game.me._dropoffs.values())
        dropoffs.extend(self.pc.ghost_dropoffs)

        dists = []
        for d in dropoffs:
            dists.append(self.gmap.calculate_distance(ship.position, d.position))

        return dropoffs[np.argmin(dists)]

    def nearest_dropoff_dist(self, cell):
        ''' Find the nearest dropoff and the distance to that dropoff''' 
        dropoffs = [self.shipyard]
        dropoffs.extend(self.game.me._dropoffs.values())
        dropoffs.extend(self.pc.ghost_dropoffs)

        dists = []
        for d in dropoffs:
            dists.append(self.gmap.calculate_distance(cell.position, d.position))

        return dropoffs[np.argmin(dists)], np.min(dists)

    def update_nearest_dropoff(self):
        ''' update the array of nearest dropoff entities'''
        for row in self.gmap._cells:
            for cell in row:
                cpos = (cell.position.y,cell.position.x)
                self.pc.nearest_dropoff[cpos] = self.nearest_dropoff(cell)

    def rev_dijk(self):
        ''' Dijkstra algorithm to compute the travel costs of moving to 
            the nearest dropoff'''
        t0 = time.time()
        graph = self.pc.mapgraph
        dropoffs = [self.game.me.shipyard]
        dropoffs.extend(self.game.me._dropoffs.values())
        dropoffs.extend(self.pc.ghost_dropoffs)

        dijk_paths = {}
        cost_at_cell = {}
        cost_cell = np.empty((self.pc.h, self.pc.w))
            
        for d in dropoffs:
            start = (d.position.y, d.position.x)
            dijk_paths[start] = None
            cost_at_cell[start] = 0
            cost_cell[start[0]][start[1]] = 0

            next_cell = []
            heapq.heappush(next_cell, (0, start))


            while next_cell:
                
                current = heapq.heappop(next_cell)[1]
                cell = self.gmap._cells[current[0]][current[1]]
                
                for neighbor in graph.neighbors[current]:
                    
                    if self.pc.nearest_dropoff[neighbor] != d:
                        continue
                    
                    ncell = self.gmap._cells[neighbor[0]][neighbor[1]]
                    dncell = self.dropoff_dist_arr[neighbor]

                    # travel cost
                    new_cost = cost_at_cell[current] \
                            + ncell.halite_amount/constants.MOVE_COST_RATIO

                    if neighbor not in cost_at_cell or new_cost < cost_at_cell[neighbor]:

                        # if dncell > 60:
                        #     cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                        #     continue

                        cost_at_cell[neighbor] = new_cost
                        cost_cell[neighbor[0]][neighbor[1]] = new_cost
                        heapq.heappush(next_cell, (new_cost, neighbor))
                        dijk_paths[neighbor] = current

        logging.warning('rev_dijk '+str(time.time() - t0))
        return cost_cell

    def dijkstra_costs(self, ship):
        ''' Dijkstra algorithm for computing the costs and paths to cells near ship'''
        graph = self.pc.mapgraph
        start = (ship.position.y, ship.position.x)

        cost_ship_cell = np.full((self.pc.h, self.pc.w), np.infty)
        cost_ship_cell[start[0]][start[1]] = 0
        
        next_cell = []
        heapq.heappush(next_cell, (0, start))

        dijk_paths = {}
        dijk_paths[start] = None
        cost_at_cell = {}
        cost_at_cell[start] = 0
        dist_at_cell = {}
        dist_at_cell[start] = 0

        shipyard = (self.shipyard.position.y, self.shipyard.position.x)

        while next_cell:
            
            current = heapq.heappop(next_cell)[1]
            cell = self.gmap._cells[current[0]][current[1]]
            
            for neighbor in graph.neighbors[current]:
                # travel cost
                new_cost = cost_at_cell[current] \
                           + cell.halite_amount/constants.MOVE_COST_RATIO

                # Don't allow paths with occupied 1st steps 
                new_dist = dist_at_cell[current] + 1

                heur = 0
                if new_dist == 1:
                    if self.pc.nplayers == 4:
                        if self.crash_mask_safe[neighbor] > 0:
                            heur += 1000
                    # elif self.pc.nplayers == 2:
                    #     if self.crash_mask_unsafe[neighbor] > 0:
                    #         enem = self.gmap._cells[neighbor[0]][neighbor[1]].enem
                    #         if ship.halite_amount > enem.halite_amount \
                    #            or self.ship_proximity[self.game.me.id][neighbor] \
                    #               <= self.enem_proximity[neighbor]:
                    #             heur += 1000

                # if new_dist < 5:
                #     ncell = self.gmap._cells[neighbor[0]][neighbor[1]]
                #     if ncell.is_occupied:
                #         if ncell.ship.owner == self.game.me.id:
                #             if ncell.ship.type == 'depositing':
                #                 heur += 100

                if neighbor not in cost_at_cell or new_cost + heur < cost_at_cell[neighbor]:
                    if  new_dist == 1:
                        ncell = self.gmap._cells[neighbor[0]][neighbor[1]]
                        if ncell.is_occupied:
                            if ncell.ship.owner == self.game.me.id:
                                if ncell.ship.type == 'mining' \
                                   or (ncell.ship.type == 'depositing' and ncell.ship.next) \
                                   or (ncell.ship.type == 'dropoff'):
                                    cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                                    continue
                            else:
                                if self.pc.nplayers == 4:
                                    if self.crash_mask_safe[neighbor] > 0:
                                        cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                                        continue


                    
                    # Don't go into the shipyard
                    if neighbor == shipyard:
                        cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                        continue
                    # Don't calculate beyond 40 cells
                    
                    if new_dist > 32:
                        cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                        continue
                    
                    # Don't calculate where we can't reach with current cargo
                    if new_cost > ship.halite_amount:
                        cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                        continue

                    dist_at_cell[neighbor] = new_dist
                    cost_at_cell[neighbor] = new_cost + heur
                    cost_ship_cell[neighbor[0]][neighbor[1]] = new_cost #+ heur
                    heapq.heappush(next_cell, (new_cost + heur, neighbor))
                    dijk_paths[neighbor] = current
        return cost_ship_cell, dijk_paths

    def astar_costs_depositing(self, ship, target):
        ''' A* algorithm for computing path from ship to target'''
        graph = self.pc.mapgraph
        start = (ship.position.y, ship.position.x)
        end = (target.y, target.x)
        
        next_cell = []
        heapq.heappush(next_cell, (0, start))

        dijk_paths = {}
        dijk_paths[start] = None
        cost_at_cell = {}
        cost_at_cell[start] = 0
        dist_at_cell = {}
        dist_at_cell[start] = 0

        while next_cell:
            
            current = heapq.heappop(next_cell)[1]
            cell = self.gmap._cells[current[0]][current[1]]
            
            if current == end:
                break

            for neighbor in graph.neighbors[current]:
                # travel cost
                new_cost = cost_at_cell[current] \
                           + cell.halite_amount/constants.MOVE_COST_RATIO

                # Don't allow paths with occupied 1st steps 
                new_dist = dist_at_cell[current] + 1

                heur = self.dropoff_dist_arr[neighbor]*0.1*self.halite_avg
                if  new_dist == 1:
                    if self.crash_mask_safe[neighbor] > 0:
                        heur += 1000

                if neighbor not in cost_at_cell or new_cost + heur < cost_at_cell[neighbor]:
                
                    # if dncell > 30:
                    #     cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                    #     continue
                    # if new_cost > ship.halite_amount:
                    #     cost_ship_cell[neighbor[0]][neighbor[1]] = np.infty
                    #     continue

                    dist_at_cell[neighbor] = new_dist
                    cost_at_cell[neighbor] = new_cost + heur
                    heapq.heappush(next_cell, (new_cost, neighbor))
                    dijk_paths[neighbor] = current
        return dijk_paths

    ##################################
    # Ship Targeting Methods
    ##################################

    def get_mining_cell_est(self, ship):
        ''' Returns the estimated maximum cell score for a given ship,
            used for the subsequent priority sorting of mining ships.
            '''

        # t_tilda
        dist_from_ship = self.dist_from_ship.get(ship.id, [])
        if dist_from_ship == []:
            diffx = np.absolute(self.pc.xcoords - ship.position.x)
            diffy = np.absolute(self.pc.ycoords - ship.position.y)
            dist_from_ship = (np.minimum(diffx, self.pc.w - diffx) + np.minimum(diffy, self.pc.h - diffy)).astype(np.float32)
            self.dist_from_ship[ship.id] = dist_from_ship

        # \tilda(H)_c
        avg_movement_cost = ((self.dropoff_dist_arr + dist_from_ship)*self.halite_avg/constants.MOVE_COST_RATIO).astype(np.float32)
    
        # H_0(t_0), halite amounts with exponential damping
        mineable_halite = self.mineable_halite.get(ship.id, [])
        if mineable_halite == []:
            max_t = np.maximum(self.pc.tcoords - dist_from_ship, 0, dtype=np.float32)
            base = (1 - 1/constants.EXTRACT_RATIO)
            exp_fac = (1 - np.power(base, max_t))
            halite_damped = exp_fac*self.halite_raw

            if self.pc.nplayers == 4:
                halite_damped = np.where(np.logical_and(self.enem_proximity >= 2, dist_from_ship < 5),
                                         halite_damped*3,
                                         halite_damped)


            mineable_halite = np.minimum(halite_damped, constants.MAX_HALITE - ship.halite_amount)
            self.mineable_halite[ship.id] = mineable_halite
        mineable_halite_adj = mineable_halite - avg_movement_cost

        denom = (((self.pc.tcoords + dist_from_ship)*constants.MAX_HALITE/(mineable_halite_adj) \
                  + self.dropoff_dist_arr)**(-1))*(1 + self.pc.concentration_fac*self.halite_conv_norm)
        
        cell_scores_est = np.where(mineable_halite_adj > 0,
                                   denom*(constants.MAX_HALITE - self.dropoff_cost_arr),
                                   np.zeros_like(denom))

        max_score = np.max(cell_scores_est)

        return max_score

    def get_centroid_score(self,centroid):
        ''' Evaluate the estimated scores of adding an additional dropoff at centroid location'''
        # distances from dropoffs
        diffx = np.absolute(self.pc.xcoords - centroid[1])
        diffy = np.absolute(self.pc.ycoords - centroid[0])
        dist_from_centroid = (np.minimum(diffx, self.pc.w - diffx) + np.minimum(diffy, self.pc.h - diffy)).astype(np.float32)

        dist_from_dropoffs = np.minimum(self.dropoff_dist_arr, dist_from_centroid)

        centroid_score = 0
        for ship in self.game.me.get_ships():
            if ship.type == 'mining':
                # t_tilda
                dist_from_ship = self.dist_from_ship.get(ship.id, [])
                if dist_from_ship == []:
                    diffx = np.absolute(self.pc.xcoords - ship.position.x)
                    diffy = np.absolute(self.pc.ycoords - ship.position.y)
                    dist_from_ship = (np.minimum(diffx, self.pc.w - diffx) + np.minimum(diffy, self.pc.h - diffy)).astype(np.float32)
                    self.dist_from_ship[ship.id] = dist_from_ship
                
                # \tilda(H)_c
                avg_movement_cost = ((dist_from_dropoffs + dist_from_ship)*self.halite_avg/constants.MOVE_COST_RATIO).astype(np.float32)
            
                # H_0(t_0), halite amounts with exponential damping
                mineable_halite = self.mineable_halite.get(ship.id, [])
                if mineable_halite == []:
                    max_t = np.maximum(self.pc.tcoords - dist_from_ship, 0, dtype=np.float32)
                    base = (1 - 1/constants.EXTRACT_RATIO)
                    exp_fac = (1 - np.power(base, max_t))
                    halite_damped = exp_fac*self.halite_raw
                    if self.pc.nplayers == 4:
                        halite_damped = np.where(np.logical_and(self.enem_proximity >= 2, dist_from_ship < 5),
                                                 halite_damped*3,
                                                 halite_damped)

                    mineable_halite = np.minimum(halite_damped, constants.MAX_HALITE - ship.halite_amount)
                    self.mineable_halite[ship.id] = mineable_halite
                mineable_halite_adj = mineable_halite - avg_movement_cost

                denom = (((self.pc.tcoords + dist_from_ship)*constants.MAX_HALITE/(mineable_halite_adj) \
                        + self.dropoff_dist_arr)**(-1))*(1 + self.pc.concentration_fac*self.halite_conv_norm)
                
                cell_scores_est = np.where(mineable_halite_adj > 0,
                                        denom*(constants.MAX_HALITE - self.dropoff_cost_arr),
                                        np.zeros_like(denom))

                centroid_score += np.max(cell_scores_est)

        return centroid_score

    def get_mining_cell_scores_paths(self,ship):
        '''Score each cell around a given ship '''
        dist_from_ship = self.dist_from_ship[ship.id]

        # H_c
        cost_ship_cell, dijk_paths = self.dijkstra_costs(ship)
        
        mineable_halite = self.mineable_halite[ship.id]
        mineable_halite_adj = mineable_halite-cost_ship_cell

        denom = (((self.pc.tcoords + dist_from_ship)*constants.MAX_HALITE/(mineable_halite_adj) \
                  + self.dropoff_dist_arr)**(-1))*(1 + self.pc.concentration_fac*self.halite_conv_norm)
        
        cell_scores = np.where(mineable_halite_adj > 0,
                                   denom*(constants.MAX_HALITE - self.dropoff_cost_arr),
                                   np.zeros_like(denom))

        if self.pc.nplayers == 4:
            cell_scores = np.where(self.crash_mask_safe > 0,
                                    np.full_like(denom, -np.infty),
                                    cell_scores)

        return cell_scores, dijk_paths


    def get_mining_target(self, ship):
        ''' Select the best target available for a mining ship'''

        cell_scores, dijk_paths = self.get_mining_cell_scores_paths(ship)

        cell_scores = np.multiply(cell_scores, self.mining_targets)
        cell_scores = np.where(np.isnan(cell_scores), 
                               np.full(cell_scores.shape, -np.infty), 
                               cell_scores)
        
        cell_scores[:,self.shipyard.position.y, self.shipyard.position.x] = -np.Infinity

        max_score = np.max(cell_scores)
        if max_score == 0:
            target_index = (0, ship.position.y, ship.position.x)
        else:
            target_index = np.unravel_index(np.argmax(cell_scores), cell_scores.shape)
        target = self.gmap._cells[target_index[1]][target_index[2]]
        target.targeted = ship

        # Other ships can no longer target this cell
        self.mining_targets[target_index[1:]] = 0

        # Traverse cheapest path to get 1st move
        shipcell = (ship.position.y, ship.position.x)
        first_step = target_index[1:]
        while dijk_paths[first_step] != shipcell and dijk_paths[first_step]:
            first_step = dijk_paths[first_step]
        direction = self.gmap.get_one_move_direction(ship.position,
                                                     Position(first_step[1], first_step[0]))
        
        return target, direction

    def get_mining_target_fast(self, ship):
        ''' Get mining target using naive method when short on time.'''
        pos = ship.position
        cell = self.gmap.__getitem__(pos)
        c = 0.1*cell.halite_amount

        if ship.halite_amount < c:
            return (0,0)

        # find safe directions
        dirs = [Direction.North, Direction.South,
                Direction.East, Direction.West, Direction.Still]
        pref = [-c, -c, -c, -c, 0]
        if cell.halite_amount <= 1:
            pfac = [1, 1, 1, 1, 0]
        else:
            pfac = [1, 1, 1, 1, 1.3]
        for i in range(len(dirs)):
            test_pos = pos.directional_offset(dirs[i])
            test_cel = self.gmap.__getitem__(test_pos)
            test_pos = (test_pos.y, test_pos.x)
            
            pref[i] += self.halite_conv_big[test_pos]
            if dirs[i] != Direction.Still:
                if test_cel.is_occupied: 
                    if test_cel.ship.type == 'mining':
                        pref[i] = -np.infty

            pref[i] *= pfac[i]

        direction = dirs[np.argmax(pref)]
    
        return direction

    def get_deposit_target(self, ship):
        ''' Get target and move for depositing ships moving to dropoff'''
        target = self.nearest_dropoff(ship).position
        target_index = (target.y, target.x)

        dijk_paths = self.astar_costs_depositing(ship, target)

        # Traverse cheapest path to get 1st move
        shipcell = (ship.position.y, ship.position.x)
        first_step = target_index
        while dijk_paths[first_step] != shipcell and dijk_paths[first_step]:
            first_step = dijk_paths[first_step]
        direction = self.gmap.get_one_move_direction(ship.position,
                                                     Position(first_step[1], first_step[0]))
        
        return target, direction
        

    ##################################
    # Ship Movement Methods
    ##################################

    def ship_can_move(self, ship):
        '''True iff ship has sufficient halite to move to next cell '''
        cell = self.gmap.__getitem__(ship.position)
        if ship.halite_amount >= 0.1*cell.halite_amount:
            return True
        else:
            return False

    def map_update_move(self, ship):
        '''Update map cell occupancies based on known prior moves'''
        cell_init = self.gmap.__getitem__(ship.position)
        cell_next = self.gmap.__getitem__(ship.next)

        cell_init.ship = None
        cell_next.ship = ship

    def map_update_move_swap(self, ship, oship):
        '''Update map cell occupancies for swapping ships.
           Redundant function.'''
        cell_init = self.gmap.__getitem__(ship.position)
        cell_next = self.gmap.__getitem__(ship.next)

        cell_init.ship = oship
        cell_next.ship = ship

    def make_move(self, ship, target):
        '''Force a particular move.'''
        # get move from navigation
        move = self.gmap.naive_navigate(ship, target)
        smove = ship.move(move)

        # update map info
        self.map_update_move(ship)

        return smove

    def make_move_depositing(self, ship):
        ''' Create a move command for depositing type ships.
            Target the nearest dropoff point. '''
        # Target nearest dropoff
        target, direction = self.get_deposit_target(ship)

        move_pos = ship.position.directional_offset(direction)
        if self.gmap[move_pos].is_occupied:
            oship = self.gmap[move_pos].ship
            if oship.owner == self.game.me.id:
                smove = ship.move(Direction.Still)
            else:
                smove = ship.move(direction)
        else:
            smove = ship.move(direction)

        # update cell occupation info
        self.map_update_move(ship)

        return smove

    def make_move_mining(self, ship, timeout = 0):
        ''' if mining ship has reached target cell, issue mining cmd,
            else advance toward target'''

        # Get target for mining
        if timeout == 0:
            target, direction = self.get_mining_target(ship) 
            target = target.position
        else:
            # Fast target selection when time is running low
            direction = self.get_mining_target_fast(ship)
            target = ship.position.directional_offset(direction)

        if ship.position == target:
            smove = ship.stay_still()
            self.map_update_move(ship)
            return smove
        else:
            # if cant move, stay still
            if not self.ship_can_move(ship):
                smove = ship.move(Direction.Still)
            else:
                smove = ship.move(direction)

                move_pos = ship.position.directional_offset(direction)
                mpos = (move_pos.y, move_pos.x)

                # Check for swapping with depositing type ships
                if self.gmap[move_pos].is_occupied:
                    oship = self.gmap[move_pos].ship
                    if oship.owner == self.game.me.id:
                        oship_type = oship.type
                    else:
                        oship_type = None
                    
                    dship = self.dropoff_dist_arr[ship.position.y][ship.position.x]
                    doship = self.dropoff_dist_arr[oship.position.y][oship.position.x]
                    if oship_type == 'depositing': 
                        if dship < doship:
                            oship.next = ship.position
                            smove = ship.move(direction)
                            self.map_update_move_swap(ship, oship)
                            return smove
                        else:
                            smove = ship.move(Direction.Still)


                # Check for enemy collision condition
                if self.pc.nplayers == 2:
                    if self.crash_mask_unsafe[mpos] > 0:
                        enem = self.gmap._cells[mpos[0]][mpos[1]].enem
                        if ship.halite_amount < enem.halite_amount \
                           and self.ship_proximity[self.game.me.id][mpos] \
                               > self.enem_proximity[mpos]:
                            smove = ship.move(direction)
                        else:
                            smove = ship.move(Direction.Still)

            self.map_update_move(ship)
            return smove

    def make_move_dropoff(self, ship):
        ''' Move the dropoff ship to the dropoff location '''
        # Get target 
        target = ship.drop
        cell = self.gmap[target]

        if ship.position == target:
            if self.game.me.halite_amount + ship.halite_amount \
               + cell.halite_amount >= 4000:
                self.pc.ghost_dropoffs = []
                self.update_nearest_dropoff()
                return ship.make_dropoff()
            else:
                return ship.stay_still()
        else:
            dijk_paths = self.astar_costs_depositing(ship, target)

            shipcell = (ship.position.y, ship.position.x)
            first_step = (target.y, target.x)
            while dijk_paths[first_step] != shipcell and dijk_paths[first_step]:
                first_step = dijk_paths[first_step]
            direction = self.gmap.get_one_move_direction(ship.position,
                                                        Position(first_step[1], first_step[0]))

            return ship.move(direction)

    def make_move_end(self, ship, target):
        ''' Moves for end_depositing type ships.
            Doesn't avoid collisions '''
        # get move from navigation
        move = self.gmap.naive_navigate_end(ship, target)
        smove = ship.move(move)

        # update map info
        self.map_update_move(ship)

        return smove
