# Write Up

## Overview

### Thoughts On The Game

### My Performance

## Details
The Halite game is complex enough that a competitor can improve their standing by enhancing any of several key components in their bot. 
Given that the game revolves around collecting the largest quantity of halite in a specified amount of time, it seemed that optimally prioritizing
cells to mine from, and allocating ships to those cells, would be the single most important aspects of a strong bot. For this reason, I spent more 
time developing the target selection strategy than any other component of my bot.

### Cell Scoring
I believed, as many competitors did, that the fundamental quantity to maximize was the halite collected per time. Within the sphere of target selection,
this takes the form of a scoring/objective function $S(c)$, where $c$ is the cell to scored. In its most basic construction, one has
$$
\begin{align}
S(c) &= \frac{H(c)}{t_d (c)}, 
\end{align}
$$
where $H(c)$ is the halite content of the cell and $t_d (c)$ is the time it would take for a ship to move from this cell to the nearest dropoff point 
(including the shipyard). This implementation has advantage of being exceedingly simple and highly interpretable. However, the interpretation -- if I 
*instaneously* mine *all* of the halite contained in this cell, I will collect halite at rate $S$ -- is not actually the one we are looking for. In fact,
we cannot instantaneously mine all of the halite contained within a cell, and we must also account for the travel time of the ship to the cell in question 
and the costs incurred in travelling. These factors, and others, add considerable complexity to the calculation and must be dealt with appropriately 
in advancing the scoring model.

In practice, ships will mine more than one cell in a round trip from a halite dropoff point. Therefore, ideally one would generalize from scoring particular
cells to scoring combinations of cells along different travel paths. A more general model with the appropriate interpretation would take the form
$$
\begin{align}
S(s,p) &= \frac{H(s,p) - T(s,p)}{t(s,p)},
\end{align}
$$
where $S(s,p)$ is the score a ship $s$ would achieve if it traveled and mined along path $p$. $H(s,p)$, $T(s,p)$, and $t(s,p)$ are the halite mined, travel costs
induced, and time in moving the ship $s$ along path $p$. One would then like to optimize over all paths $p$ for a given ship $s$. This, as far as I know, is not a 
possible computation given the constraints of the game (e.g., the time limit of 2 seconds per turn), and so simplifications and approximations are necessary in order
to prune the space of possible solutions to a managable level. I believe that some of the top competitors took this approach, which is why relatively fast languages
like C++ and Java dominate the upper end of the leaderboard. I was not able to optimize my Python code to the point where moving beyond single cell calculations was 
a feasible strategy, so I reduced the model to single cell calculations and approximated the effects of additional cells,
$$
\begin{align}
S(c) &= \frac{H(c) - T(s,c) - T(c,d) + \sum\limits_{c'} \big(H(c') - T(c')\big)}{t(s,c) + t_m(c) + t(c,d) + \sum\limits_{c'} \big(t_c(c') + t(c')\bigg)},
\end{align}
$$

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
