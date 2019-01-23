#!/usr/bin/env python3
# Python 3.6

import hlt # Import the Halite SDK, which will let you interact with the game.
from hlt import constants # This library contains constant values.
from hlt.positionals import Direction # This library contains direction metadata to better interface with the game.
import random  # This library allows you to generate random numbers.
import logging # Logging allows you to save messages for yourself. This is required because the regular STDOUT
               # (print statements) are reserved for the engine-bot communication.
import time
import heapq

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()

# Pre-game computations
pc = hlt.state.Precomp(game)

game.ready("botv14")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    
    game.update_frame()
    start = time.time() #Turn starts after update frame
    
    me = game.me
    game_map = game.game_map

    ts = time.time()
    n_drop = 0
    gstate = hlt.state.GameState(game, pc)
    logging.info('gstate time: '+str(time.time()-ts))

    command_queue = []
    while (gstate.ships_mining) or (gstate.ships_deposit) \
          or (gstate.ships_enddepo) or (gstate.ships_dropoff):

        # Dropoff Commands
        n_drop = len(gstate.ships_dropoff)
        while (gstate.ships_dropoff):
            ship = heapq.heappop(gstate.ships_dropoff)

            smove = gstate.make_move_dropoff(ship)
            command_queue.append(smove)
            continue

        # Mining Commands
        n_mine = len(gstate.ships_mining)
        tm = time.time()
        while (gstate.ships_mining):
            if time.time()-start > 1.87:
                logging.warning('OUT OF TIME, mining')
                break
            ship = heapq.heappop(gstate.ships_mining)

            if (time.time()-start > 1.82) \
               or (gstate.turn > 300 and ship.halite_amount < 50):
                smove = gstate.make_move_mining(ship, timeout=1)
            else:
                smove = gstate.make_move_mining(ship)
            command_queue.append(smove)
            continue
        mining_time = time.time() - tm
        logging.info('mining_time: '+str(mining_time)+' ' \
                     +str(mining_time/max(1, n_mine)) +' '+ str(n_mine))

        # Depositing Commands
        n_depo = len(gstate.ships_deposit)
        td = time.time()
        while (gstate.ships_deposit):
            if time.time()-start > 1.92:
                logging.warning('OUT OF TIME, depositing')
                break
            ship = heapq.heappop(gstate.ships_deposit)

            if ship.next:
                move = game_map.get_unsafe_moves(ship.position, ship.next)[0]
                smove = ship.move(move)
            else:
                # Get ship movement command for depositing type
                smove = gstate.make_move_depositing(ship)

            command_queue.append(smove)
            continue
        depo_time = time.time() - td
        logging.info('depositing_time: '+str(depo_time)+ ' '\
                      +str(depo_time/max(1, n_depo)) + ' ' + str(n_depo))

        # End_Depositing Commands
        while (gstate.ships_enddepo):
            ship = heapq.heappop(gstate.ships_enddepo)

            target = gstate.nearest_dropoff(ship)

            smove = gstate.make_move_end(ship, target.position)
            command_queue.append(smove)
            continue

        if time.time()-start > 1.87:
                logging.warning('OUT OF TIME, main loop')
                break
    
    # Ship spawning conditions
    if n_drop == 0:
        if pc.nplayers == 2:
            if    (gstate.enemy_nships_max + 1 > gstate.nships and game.turn_number <= constants.MAX_TURNS - 300) \
            or (gstate.enemy_nships_max + 1 > gstate.nships and game.turn_number <= constants.MAX_TURNS - 200) \
            or (gstate.enemy_nships_max + 0 > gstate.nships and game.turn_number <= constants.MAX_TURNS - 100):
                if me.halite_amount >= constants.SHIP_COST \
                and not game_map[me.shipyard].is_occupied \
                and time.time()-start < 1.7:
                    command_queue.append(me.shipyard.spawn())
        elif pc.nplayers == 4:
            if  gstate.halite_total/(gstate.ships_total) > 900:
                if me.halite_amount >= constants.SHIP_COST \
                and not game_map[me.shipyard].is_occupied \
                and time.time()-start < 1.7:
                    command_queue.append(me.shipyard.spawn())

    # Local Spawns, only for testing on my local machine
    # if game.turn_number <= 200 \
    #     and me.halite_amount >= constants.SHIP_COST \
    #     and not game_map[me.shipyard].is_occupied \
    #     and time.time()-start < 1.86:
    #     command_queue.append(me.shipyard.spawn())

    logging.info('Time Elapsed: '+str(time.time()-start))
    # Submit commands/End turn
    game.end_turn(command_queue)


