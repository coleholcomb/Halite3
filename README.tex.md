# Write Up

## Overview

## Details: Cell Scoring
The Halite game is complex enough that a competitor can improve their standing by enhancing any of several key components in their bot. 
Given that the game revolves around collecting the largest quantity of halite in a specified amount of time, it seemed that optimally prioritizing
cells to mine from, and allocating ships to those cells, would be the single most important aspects of a strong bot. For this reason, I spent more 
time developing the target selection strategy than any other component of my bot.

I believed, as many competitors did, that the fundamental quantity to maximize was the halite collected per time. Within the sphere of target selection,
this takes the form of a scoring/objective function $S(c)$, where $c$ is the cell to scored. In its most basic construction, one has
$$
\begin{align}
S(c) &= \frac{H_{c}}{t_d}, 
\end{align}
$$
where $H_c$ is the halite content of the cell and $t_d$ is the time it would take for a ship to move from this cell to the nearest dropoff point (including the shipyard).

$$
\begin{align}
S (c) &=  \max\limits_{t_m} S(c, t_{\rm m}) \\
 S(c, t_{\rm m}) &= \frac{H_{\rm c}(t_{\rm c}, t_{\rm m}) - T_{\rm c}}{t_{\rm m} + t_c}\bigg[ \frac{1 + \frac{\sum_{\rm c' \ne c}  H_{\rm c'} - T_{\rm c'}}{}}{}\bigg] 
\end{align}
$$

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
