# Worldle unlimited

[Worldle](https://worldle.teuteuf.fr/) is a game where you must guess a country from its outline. You can only play this game once every day.

In this repository, we implemented using Python & Dash a simple game where you have to guess a country from its outlines or its flag. However, here, you can guess as many countries as you wish.

![Outline Image](https://github.com/Horace-BELOT/worldle-unlimited/blob/master/files/images_readme/example_outline.png)

![Flag Image](https://github.com/Horace-BELOT/worldle-unlimited/blob/master/files/images_readme/example_flag.png)

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Output:
```bash
Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'main'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:8050
Press CTRL+C to quit
```
Then simply go to [http://127.0.0.1:8050/](http://127.0.0.1:8050/) (might be different on your machine).

## Data

### Outline data

The outline data comes from [naturalearthdata.com](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/).

In order to obtain correct data, we have to combine the data if countries without the bordering lakes and the data that splits some countries from their far-away territories. This allows us to have both countries with their border stopping at neighboring lakes (which is a must have for countries like Tanzania, Turkmenistan or Nicaragua), and to have, for example, France split between mainland, French Guyana, and its other territories.

### Flag data

Flags, capitals and continents are scrapped from [Flagpedia](https://flagpedia.net/).

## Improvements to implement

- Offer the option to remove the already guessed countries from the dropdown
- Offer the option to allow multiple guesses before moving to the next country
- Find better outlines for very small countries with easy-to-distinguish outlines like Monaco.