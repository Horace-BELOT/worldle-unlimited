# Worldle unlimited

[Worldle](https://worldle.teuteuf.fr/) is a game where you must guess a country from its outline. You can only play this game once every day.

In this repository, we implemented using Python & Dash a simple game where you have to guess a country from its outlines or its flag. However, here, you can guess as many countries as you wish.

![Outline Image](https://github.com/Horace-BELOT/worldle-unlimited/blob/master/files/images_readme/example_outline.png)

![Flag Image](https://github.com/Horace-BELOT/worldle-unlimited/blob/master/files/images_readme/example_flag.png)


## Data

The data comes from naturalearthdata.com : 

https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/

In order to obtain correct data, we have to combine the data if countries without the bordering lakes and the data that splits some countries from their far-away territories. This allows us to have both countries with their border stopping at neighboring lakes (which is a must have for countries like Tanzania), and to have, for example, France split between mainland, French Guyana, and its other territories.

## Improvements to implement

- Offer the option to remove the already guessed countries from the dropdown
- Offer the option to allow multiple guesses before moving to the next country