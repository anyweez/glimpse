## Glimpse
### Procedural world generation

I've wanted to generate my own virtual worlds for a long time but haven't had much background on how to pursue it; this project demonstrates my latest progress. You can read more on the goals of this project [here](https://lukesegars.com/posts/foundations-of-world-generation), and I'm writing up lessons learned for others in [the wiki](https://github.com/anyweez/glimpse/wiki).

There are tons of great resources online for world generation, and many of the good ideas I've implemented have come from more experienced minds. You can see acknowledgements (and good links to learn from!) below.

<table>
  <tr>
    <td> <img src="https://anyweez.github.io/glimpse/img/terrain-1.png" alt="Drawing" style="width: 250px;"/> </td>
    <td> <img src="https://anyweez.github.io/glimpse/img/terrain-2.png" alt="Drawing" style="width: 250px;"/> </td>
  </tr>
</table>

### Overview of PCG

[Procedural content generation](https://en.wikipedia.org/wiki/Procedural_generation) describes a process that generates data programmatically instead of manually; its commonly applied in video games and other forms of entertainment. I love it because it forces you to understand and represent systems -- to form lakes in a virtual world, you need to understand how lakes form in real life (at least well enough to fake it).

### Project overview

This project generates virtual worlds from nothing and produces outputs in PNG and SVG format. Generated worlds may include forests, terrain, cities from one or more cultures (with generated names), rivers, named mountains and lakes, and other interesting features. Most world generation logic is
stored in **plug-ins** to make it easier to reason about and learn from.

If you're trying to learn PCG from this project, start with the wiki or the acknowledgement links below.

### Acknowledgements

Thanks to all who have taken the time to share their expertise. The following resources have been helpful as I've found my way:

* [Red Blob Games](https://www.redblobgames.com/), especially [this](http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/) and [this](https://www.redblobgames.com/maps/terrain-from-noise/).
* [Martin O'Leary's](http://mewo2.com/notes/terrain/) generator
* [Scott Turner's site](https://heredragonsabound.blogspot.com/), which he actively maintains
* [Azgaar's blog](https://azgaar.wordpress.com/)