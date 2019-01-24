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
*instantaneously* mine *all* of the halite contained in this cell, I will collect halite at rate <img src="/tex/e257acd1ccbe7fcb654708f1a866bfe9.svg?invert_in_darkmode&sanitize=true" align=middle width=11.027402099999989pt height=22.465723500000017pt/> -- is not actually the one we are looking for. In fact,
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
<p align="center"><img src="/tex/5ea6dcd3cf295263b411d578222ac89c.svg?invert_in_darkmode&sanitize=true" align=middle width=382.14109394999997pt height=63.59824185pt/></p>

where <img src="/tex/46274a64e8b70f2d22618780e7ee8da1.svg?invert_in_darkmode&sanitize=true" align=middle width=34.899206099999994pt height=24.65753399999998pt/> is the halite mined at cell <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/>, <img src="/tex/3e3b4e41f04930951208d0833e2c801c.svg?invert_in_darkmode&sanitize=true" align=middle width=47.72457854999999pt height=24.65753399999998pt/> are the travel costs incurred in traveling from point <img src="/tex/44bc9d542a92714cac84e01cbbb7fd61.svg?invert_in_darkmode&sanitize=true" align=middle width=8.68915409999999pt height=14.15524440000002pt/> to  point <img src="/tex/4bdc8d9bcfb35e1c9bfb51fc69687dfc.svg?invert_in_darkmode&sanitize=true" align=middle width=7.054796099999991pt height=22.831056599999986pt/> (the symbol <img src="/tex/6f9bad7347b91ceebebd3ad7e6f6f2d1.svg?invert_in_darkmode&sanitize=true" align=middle width=7.7054801999999905pt height=14.15524440000002pt/> standing in for the location of the ship),
<img src="/tex/15d283564c9146ec18312a86d154bc25.svg?invert_in_darkmode&sanitize=true" align=middle width=41.77136534999999pt height=24.65753399999998pt/> is the travel time from <img src="/tex/44bc9d542a92714cac84e01cbbb7fd61.svg?invert_in_darkmode&sanitize=true" align=middle width=8.68915409999999pt height=14.15524440000002pt/> to <img src="/tex/4bdc8d9bcfb35e1c9bfb51fc69687dfc.svg?invert_in_darkmode&sanitize=true" align=middle width=7.054796099999991pt height=22.831056599999986pt/>, and <img src="/tex/cd735f39f70cf5bcf309806805ae68ae.svg?invert_in_darkmode&sanitize=true" align=middle width=38.322099749999985pt height=24.65753399999998pt/> is the time spent mining cell <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/>. The inclusion of secondary, tertiary, etc... cells is encapsulated by the sum over <img src="/tex/3ce681234d1b2ad17008503143e3ed8b.svg?invert_in_darkmode&sanitize=true" align=middle width=10.90376594999999pt height=24.7161288pt/>. With
the exception of the <img src="/tex/4de4455edd7c13edb02ba04a7c447d90.svg?invert_in_darkmode&sanitize=true" align=middle width=47.65039454999999pt height=24.65753399999998pt/> and <img src="/tex/7db24b7ec18e3b9d53da12112b2831e3.svg?invert_in_darkmode&sanitize=true" align=middle width=41.69718134999999pt height=24.65753399999998pt/> terms (i.e., using the cost and travel time of return to the dropoff from the primary cell <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/>), this an equivalent representation of
<img src="/tex/9cb59705b5afe98b70cd0b5cb129d6a2.svg?invert_in_darkmode&sanitize=true" align=middle width=120.09831899999998pt height=33.51592530000001pt/>, where <img src="/tex/b17e856e76ef58f7655e6ace49d21d06.svg?invert_in_darkmode&sanitize=true" align=middle width=14.14521899999999pt height=14.15524440000002pt/> is the path to <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/> and <img src="/tex/4ae3393b40dfbbbc0932cf55cbc55bc3.svg?invert_in_darkmode&sanitize=true" align=middle width=12.060528149999989pt height=24.7161288pt/> can be any path starting at <img src="/tex/3e18a4a28fdee1744e5e3f79d13b9ff6.svg?invert_in_darkmode&sanitize=true" align=middle width=7.11380504999999pt height=14.15524440000002pt/> and ending at a dropoff, assuming that you know what the optimal cells <img src="/tex/3ce681234d1b2ad17008503143e3ed8b.svg?invert_in_darkmode&sanitize=true" align=middle width=10.90376594999999pt height=24.7161288pt/> are.

As stated above, it was not feasible to calculate the optimal <img src="/tex/3ce681234d1b2ad17008503143e3ed8b.svg?invert_in_darkmode&sanitize=true" align=middle width=10.90376594999999pt height=24.7161288pt/>. Instead, we make some assumptions to simplify the sum terms into viable forms.
The first assumption is that a ship will seek to maximize its halite cargo before returning, so that
<p align="center"><img src="/tex/c5d2b5d48a500c0c78e522c24eeeb008.svg?invert_in_darkmode&sanitize=true" align=middle width=339.7335645pt height=36.8951715pt/></p>

where <img src="/tex/35cc71776e172499f645e66424105c57.svg?invert_in_darkmode&sanitize=true" align=middle width=93.53890259999999pt height=22.465723500000017pt/> is the maximum amount of halite an individual ship can carry at a time. This assumption reduces the numerator of <img src="/tex/2a2ac6cebda315d6c50722c2181d9e3d.svg?invert_in_darkmode&sanitize=true" align=middle width=30.926619899999988pt height=24.65753399999998pt/> to <img src="/tex/58ccbe88cdade1273da106638cdf7ffd.svg?invert_in_darkmode&sanitize=true" align=middle width=106.48602029999998pt height=24.65753399999998pt/>.
In order to reduce the denominator, we assume that the travel and mining times for the additional cells will be about the same as those of the primary cell, such that
a full path will include <img src="/tex/2ddd0c01fe3ca1a282413e9ceb252037.svg?invert_in_darkmode&sanitize=true" align=middle width=195.60703469999999pt height=27.94539330000001pt/> mining sites,
<p align="center"><img src="/tex/0ad761f4b5f59cce1ec3fb3e232a4b16.svg?invert_in_darkmode&sanitize=true" align=middle width=290.11760415pt height=36.8951715pt/></p>

Combining these approximations, the full score is
<p align="center"><img src="/tex/6699d0cbc6d591d6317efac378048b06.svg?invert_in_darkmode&sanitize=true" align=middle width=471.2058087pt height=38.83491479999999pt/></p>
<p align="center"><img src="/tex/f8bfc3a483b0e785ac7c71bc777479cb.svg?invert_in_darkmode&sanitize=true" align=middle width=0.0pt height=0.0pt/></p>
<p align="center"><img src="/tex/c15cd462fa67be55b5d1f0fdffda9c5f.svg?invert_in_darkmode&sanitize=true" align=middle width=515.8157433pt height=78.7738347pt/></p>
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
