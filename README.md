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
this takes the form of a scoring/objective function <img src="/tex/2a2ac6cebda315d6c50722c2181d9e3d.svg?invert_in_darkmode&sanitize=true" align=middle width=30.926619899999988pt height=24.65753399999998pt/>, where <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/> is the cell to scored. In its most basic construction, one has
<p align="center"><img src="/tex/9fc6ec3aaa0b07d92cd7b132f128747f.svg?invert_in_darkmode&sanitize=true" align=middle width=96.25481414999999pt height=38.83491479999999pt/></p>
where <img src="/tex/46274a64e8b70f2d22618780e7ee8da1.svg?invert_in_darkmode&sanitize=true" align=middle width=34.899206099999994pt height=24.65753399999998pt/> is the halite content of the cell and <img src="/tex/b3b55c29da398f33fb85c53847cf79e7.svg?invert_in_darkmode&sanitize=true" align=middle width=33.50033114999999pt height=24.65753399999998pt/> is the time it would take for a ship to move from this cell to the nearest dropoff point 
(including the shipyard). This implementation has advantage of being exceedingly simple and highly interpretable. However, the interpretation -- if I 
*instaneously* mine *all* of the halite contained in this cell, I will collect halite at rate <img src="/tex/e257acd1ccbe7fcb654708f1a866bfe9.svg?invert_in_darkmode&sanitize=true" align=middle width=11.027402099999989pt height=22.465723500000017pt/> -- is not actually the one we are looking for. In fact,
we cannot instantaneously mine all of the halite contained within a cell, and we must also account for the travel time of the ship to the cell in question 
and the costs incurred in travelling. These factors, and others, add considerable complexity to the calculation and must be dealt with appropriately 
in advancing the scoring model.

In practice, ships will mine more than one cell in a round trip from a halite dropoff point. Therefore, ideally one would generalize from scoring particular
cells to scoring combinations of cells along different travel paths. A more general model with the appropriate interpretation would take the form
<p align="center"><img src="/tex/c2107768b733c965c56abb547207bf90.svg?invert_in_darkmode&sanitize=true" align=middle width=196.63885065pt height=38.83491479999999pt/></p>
where <img src="/tex/520b5fc6ec14c91455e2fcf2ace53419.svg?invert_in_darkmode&sanitize=true" align=middle width=47.09474549999999pt height=24.65753399999998pt/> is the score a ship <img src="/tex/6f9bad7347b91ceebebd3ad7e6f6f2d1.svg?invert_in_darkmode&sanitize=true" align=middle width=7.7054801999999905pt height=14.15524440000002pt/> would achieve if it traveled and mined along path <img src="/tex/2ec6e630f199f589a2402fdf3e0289d5.svg?invert_in_darkmode&sanitize=true" align=middle width=8.270567249999992pt height=14.15524440000002pt/>. <img src="/tex/6fa93f442c42ae006141f1cc5567e25a.svg?invert_in_darkmode&sanitize=true" align=middle width=51.06733169999999pt height=24.65753399999998pt/>, <img src="/tex/560617f2ebc595b0ba857a0f4946cc03.svg?invert_in_darkmode&sanitize=true" align=middle width=47.95667414999999pt height=24.65753399999998pt/>, and <img src="/tex/78a9fbddc3e62359af9441f1cb56c722.svg?invert_in_darkmode&sanitize=true" align=middle width=42.00346094999999pt height=24.65753399999998pt/> are the halite mined, travel costs
induced, and time in moving the ship <img src="/tex/6f9bad7347b91ceebebd3ad7e6f6f2d1.svg?invert_in_darkmode&sanitize=true" align=middle width=7.7054801999999905pt height=14.15524440000002pt/> along path <img src="/tex/2ec6e630f199f589a2402fdf3e0289d5.svg?invert_in_darkmode&sanitize=true" align=middle width=8.270567249999992pt height=14.15524440000002pt/>. One would then like to optimize over all paths <img src="/tex/2ec6e630f199f589a2402fdf3e0289d5.svg?invert_in_darkmode&sanitize=true" align=middle width=8.270567249999992pt height=14.15524440000002pt/> for a given ship <img src="/tex/6f9bad7347b91ceebebd3ad7e6f6f2d1.svg?invert_in_darkmode&sanitize=true" align=middle width=7.7054801999999905pt height=14.15524440000002pt/>. This, as far as I know, is not a 
possible computation given the constraints of the game (e.g., the time limit of 2 seconds per turn), and so simplifications and approximations are necessary in order
to prune the space of possible solutions to a managable level. I believe that some of the top competitors took this approach, which is why relatively fast languages
like C++ and Java dominate the upper end of the leaderboard. I was not able to optimize my Python code to the point where moving beyond single cell calculations was 
a feasible strategy, so I reduced the model to single cell calculations and approximated the effects of additional cells,
<p align="center"><img src="/tex/b7c54c46b4036907895744e6f472bdfb.svg?invert_in_darkmode&sanitize=true" align=middle width=382.14109394999997pt height=74.37473175pt/></p>

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
