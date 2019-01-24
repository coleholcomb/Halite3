# Write Up

## Overview

## Details: Cell Scoring
The Halite game is complex enough that a competitor can improve their standing by enhancing any of several key components in their bot. 
Given that the game revolves around collecting the largest quantity of halite in a specified amount of time, it seemed that optimally prioritizing
cells to mine from, and allocating ships to those cells, would be the single most important aspects of a strong bot. For this reason, I spent more 
time developing the target selection strategy than any other component of my bot.

I believed, as many competitors did, that the fundamental quantity to maximize was the halite collected per time. Within the sphere of target selection,
this takes the form of a scoring/objective function <img src="/tex/2a2ac6cebda315d6c50722c2181d9e3d.svg?invert_in_darkmode&sanitize=true" align=middle width=30.926619899999988pt height=24.65753399999998pt/>, where <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/> is the cell to scored. In its most basic construction, one has
<p align="center"><img src="/tex/4380b1a37d943e0a85bd10f98e4ac9ec.svg?invert_in_darkmode&sanitize=true" align=middle width=81.71659155pt height=36.09514755pt/></p>
where <img src="/tex/f8eae07bbbb80f68e9f0ee10c343cb7d.svg?invert_in_darkmode&sanitize=true" align=middle width=19.53905414999999pt height=22.465723500000017pt/> is the halite content of the cell and <img src="/tex/d4e86f88591cd633586e44f41f2a9be8.svg?invert_in_darkmode&sanitize=true" align=middle width=12.77917574999999pt height=20.221802699999984pt/> is the time it would take for a ship to move from this cell to the nearest dropoff point (including the shipyard).

<p align="center"><img src="/tex/a91743d545c46fcecc0eade8ef2467c5.svg?invert_in_darkmode&sanitize=true" align=middle width=331.35747645pt height=78.7738347pt/></p>

## Next Steps
* Better depositing conversion
* Other ship types
* Implement dropoffs

## Version History
* botv14 (final)
  * fixed bug in cell scoring around dropoffs
  * adjusted 4p dropoff locations
  * added untested inspiration boosting in 4p
  * increased cluster affinity in 4p
  * created "fast" move for mining ships when timeouts are on the line
  * changed 4p ship spawning strategy
* botv13drop
  * rudimentary dropoff spawning
* botv12
  * 2p enemy crashing strategy
  * linear cluster score scaling
* botv11
  * 4p depositing ships no longer crash into enemies.
* botv10
  * Simple 4p crash detection
* botv9
  * Cluster scoring = 0.5
* botv8
  * Increased time efficiency, fixed game_update timing bug
* botv7
  * Fixed bug where mining ship gets stuck on shipyard
  * Changed deposit converstion condition to 0.95
* botv6
  * Depositing ships now use A* -> less clumping
  * v5 - 32: 5/5, 40: 8/2, 48: 6/4
* botv5
  * Dropoff blocking defense
  * Prioritize cells that can be reached in mining cell selection
  * Mining ships avoid depositing paths with 100 halite heuristic
* botv4
  * Dijkstra based pathfinding and cell scoring for mining
  * Dijkstra based pathfinding for depositing
* botv3
  * Changed mining->deposit converstion minimum to 85% capacity
* botv2
  * Change mining->deposit converstion minimum to 66% capacity 
  * Reversed order of mining and depositing commands for more efficient deposition
  * Role swapping (depositing -> mining) is performed prior to command loop
* botv1
  * Basic role assignment
  * Primitive mining selection
  * Naive deposit
