# Post-Mortem: A top 100 bot in 10 days

## Overview

This is my submission to the [Halite 3](halite.io) competition, hosted by [Two Sigma](https://www.twosigma.com/). My profile is [here](https://halite.io/user/?user_id=562).
Unfortunately, I was not able to participate in the ~3 month competition until 10 days before the final submission deadline. Given the time I had available, I focused my time on
the one or two aspects that I believed were the most important of creating a strong bot. As of this writing, my submission is sitting around rank ~90, with some uncertainty as 
the final round plays out.

Most of my time was spent on optimizing target selection (detailed below) and on ship navigation. These features allow my bot to have a relatively strong early-game which
typically gives me a slight edge in the first 100 turns. At the highest ranks, mid- and late-game seems to be dominated by exploitation of the inspiration and dropoff mechanics,
which I was only able to naively implement in the final day of the competition, and ship micro-management around enemy ships, which I did not implement at all. I only had time to make
use of inspiration in my 4-player game strategy, and hence my 4-player win rate is carrying my ranking while my 2-player win rate is abysmal. However, my presence in the top 100
indicates that it is possible to get very far while concentrating only on one or two aspects of the game and maintaining only rudimentary implementations of the others. 

## Details: Cell Scoring
The Halite game is complex enough that a competitor can improve their standing by enhancing any of several key components in their bot. 
Given that the game revolves around collecting the largest quantity of halite in a specified amount of time, it seemed that optimally prioritizing
cells to mine from, and allocating ships to those cells, would be the single most important aspects of a strong bot. For this reason, I spent more 
time developing the target selection (cell scoring) strategy than any other component of my bot, and provide details below.

I believed, as many competitors did, that the fundamental quantity to maximize was the halite collected per time. Within the sphere of target selection,
this takes the form of a scoring/objective function $S(c)$, where $c$ is the cell to scored. In its most basic construction, one has
$$
\begin{align}
S(c) &= \frac{H(c)}{t_d (c)}, 
\end{align}
$$

where $H(c)$ is the halite content of the cell and $t_d (c)$ is the time it would take for a ship to move from this cell to the nearest dropoff point 
(including the shipyard). This implementation has advantage of being exceedingly simple and highly interpretable. However, the interpretation -- if I 
*instantaneously* mine *all* of the halite contained in this cell, I will collect halite at rate $S$ -- is not actually the one we are looking for. In fact,
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
to prune the space of possible solutions to a managable level. I believe that a few of the top competitors took this approach, which is why relatively fast languages
like C++ and Java dominate the upper end of the leaderboard. I was not able to optimize my Python code to the point where moving beyond single cell calculations was 
a feasible strategy, so I reduced the model to single cell calculations and approximated the effects of additional cells,
$$
\begin{align}
S(c) &= \frac{H(c) - T(s,c) - T(c,d) + \sum\limits_{c'} \big(H(c') - T(c')\big)}{t(s,c) + t_m(c) + t(c,d) + \sum\limits_{c'} \big(t_c(c') + t_m(c')\big)},
\end{align}
$$

where $H(c)$ is the halite mined at cell $c$, $T(a,b)$ are the travel costs incurred in traveling from point $a$ to  point $b$ (the symbol $s$ standing in for the location of the ship),
$t(a,b)$ is the travel time from $a$ to $b$, and $t_m (c)$ is the time spent mining cell $c$. The inclusion of secondary, tertiary, etc... cells is encapsulated by the sum over $c'$. With
the exception of the $T(c,d)$ and $t(c,d)$ terms (i.e., using the cost and travel time of return to the dropoff from the primary cell $c$), this an equivalent representation of
$\max\limits_p' S(s,p_c + p')$, where $p_c$ is the path to $c$ and $p'$ can be any path starting at $c$ and ending at a dropoff, assuming that you know what the optimal cells $c'$ are.

As stated above, it was not feasible to calculate the optimal $c'$. Instead, we make some assumptions to simplify the sum terms into viable forms.
The first assumption is that a ship will seek to maximize its halite cargo before returning, so that
$$
\begin{align}
\sum\limits_{c'} \big(H(c') - T(c')\big) &\approx H_{\rm max} - \big(H(c) - T(s,c)\big),
\end{align}
$$

where $H_{\rm max} = 1000$ is the maximum amount of halite an individual ship can carry at a time. This assumption reduces the numerator of $S(c)$ to $H_{\rm max} - T(c,d)$.
In order to reduce the denominator, we assume that the travel and mining times for the additional cells will be about the same as those of the primary cell, such that
a full path will include $n \equiv H_{\rm max}/\big(H(c) - T(s,c)\big)$ mining sites,
$$
\begin{align}
 \sum\limits_{c'} \big(t_c(c') + t_m(c')\big) &\approx n\big(t(s,c) + t_m(c)\big).
\end{align}
$$


Combining the above approximations, the score is
$$
\begin{align}
S(c, t_m) &\approx \frac{H_{\rm max} - T(c,d)}{n\big(t(s,c) + t_m(c)\big) + t(c,d)}.
\end{align}
$$

Up to this point we have ignored an important nuance: what is $H(c)$? In fact, this is a time dependent quantity that increases nonlinearly with $t_m$,
$$
H(c, t_m) &= (1- 0.75^{\max \big(0, t_m - t(s,c)\big)}).
$$

To find the best score, we maximize each cell over $t_m$
$$
\begin{align}
S (c) &=  \max\limits_{t_m} S(c, t_{\rm m}).
\end{align}
$$

It can be shown that there is a value of $t_m$ that maximizes the halite collected per time. In practice, I looked for the maximum score over an 
$N_t \times H \times W$ matrix, where $N_t = 60$ is the maximum value of $t_m + t(s,c)$ that I computed scores for,
and $H$ and $W$ are the height and width of the map.

The score derived above is not the end of the story. Heuristics were included to capitilize on the inspiration mechanic (4p only) and to
increase priority to dense halite regions (decreasing travel time on secondary+ cells). Unfortunately these multipliers are not well motivated like the above
discussion, and I was only able to tinker with them in the final day. As a result, their values are likely far from optimal and there is not much room for 
explanation. Additionally, it should be noted that ``halite collected per turn" is not precisely the correct quantity to maximize, since there is also an
advantage in returning the halite to the dropoffs sooner rather than later. This could likely be captured with some scoring heuristic, but I did not get around
to implementing one.

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
  * Basic ship role assignment
  * Primitive mining selection
  * Naive deposit
