import { CurrencyPipe, KeyValuePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, signal } from '@angular/core';

interface PokemonObject {
  image: string;
  price ?: number | string;
  cardType ?: string;
}

@Component({
  selector: 'app-home-page',
  imports: [KeyValuePipe, CurrencyPipe],
  templateUrl: './home-page.component.html',
  styleUrl: './home-page.component.css'
})
export class HomePageComponent {

  constructor(private http: HttpClient) {}

  showSearchResults = signal<boolean>(false);
  pokemonInput = signal<string>('');

  images: { [key: string]: PokemonObject } = {}; //key is a variable of type string, value holds string

  getImagesLength(){
    return Object.keys(this.images).length;
  }

  getPokemonImage(){
    // const inputElement = event.target as HTMLInputElement;
    if (this.pokemonInput() === ''){
      console.log('Input is empty');
      return;
    }
    let url = `https://api.pokemontcg.io/v2/cards?q=name:${this.pokemonInput()}`;


    this.http.get(url).subscribe((response: any) => {
      console.log(response);

      // get 3 random cards from the response
      if (response.data.length < 3) {
        console.log('Not enough cards found');
        this.showSearchResults.set(false);
        return;
      }
      const randomIndices = new Set<number>();
      while (randomIndices.size < 3) {
        const randomIndex = Math.floor(Math.random() * response.data.length);
        randomIndices.add(randomIndex);
      }
      console.log('Random indices: ', Array.from(randomIndices));
      console.log('Response data length: ', response.data.length);

      this.images = {} // Clear previous images
      for ( const i of randomIndices) {
        if( response.data[i] && response.data[i].images && response.data[i].images.large) {
          //get the price object for the card price and card type
          let priceKeys : any = Object.keys(response.data[i].tcgplayer.prices); //access price keys as strings in array:'normal', 'holofoil', etc.
          let priceHolder = "N/A";
          let cardTypeHolder = "";
          if(priceKeys.length !== 0) {
            cardTypeHolder = priceKeys[0]; //returns string
            let priceCardType = Object.keys(response.data[i].tcgplayer.prices[cardTypeHolder]); //returns string array of price card types: 'market', 'low', 'high', etc.
            if(priceCardType.length !== 0) {
              priceHolder = response.data[i].tcgplayer.prices[cardTypeHolder][priceCardType[0]]; //returns the first price type, Ex: 'market'
            }
            console.log('Card Type: ' + cardTypeHolder + ' Price: ' + priceHolder);
          }

          //generate a random id for the image and populate the class images object
          let id = crypto.randomUUID();
          this.images[id] = {
            image: response.data[i].images.large,
            price: priceHolder,
            cardType: cardTypeHolder
          };

          //loop through the class images object and log the key, image, and price
          // const key = Object.keys(this.images)[i];
          console.log(id + ' ' + this.images[id].image + ' ' + this.images[id].price);
          this.showSearchResults.set(true);

        }

      }
    })

  }


}
