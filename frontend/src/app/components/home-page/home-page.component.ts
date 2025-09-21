import { CurrencyPipe, KeyValuePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, signal } from '@angular/core';
import { first } from 'rxjs';

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

  showHowToPlay = signal<boolean>(false);
  showSearchResults = signal<boolean>(false);
  showPlayState = signal<boolean>(false);
  pokemonInput = signal<string>('');
  imageID : number = 0; 
  answered = signal<boolean>(false);
  answeredCorrect = signal<boolean>(false);
  gameOver = signal<boolean>(false);
  successfulAdds = signal<number>(0);
  score = signal<number>(0);
  isLoading = signal<boolean>(false);
  isSecondCardLoading = signal<boolean>(false);

  arrayOfPokemonWithHyphens: string[] = [
    'Ho-Oh', 'Porygon-Z', 'Jangmo-o', 'Hakamo-o', 'Kommo-o',
    'Ting-Lu', 'Chien-Pao', 'Wo-Chien', 'Chi-Yu']

  imageObject: { [key: string | number]: PokemonObject } = {}; //key is a variable of type string, value holds string
  gameStateCompareSet : Set<{ [key: number]: PokemonObject }> = new Set(); //set to hold the images object, used to compare if the game state has changed


  getImagesLength(){
    return Object.keys(this.imageObject).length;
  }

  addImageObject(setInput : { [key: number]: PokemonObject }) : Promise<boolean>  {
    return new Promise((resolve, reject) => {
      // let POKEAPI_BASE = 'https://pokeapi.co/api/v2/pokemon';
      // const randomIndex = Math.floor(Math.random() * 1024);
      // const pokeUrl = `${POKEAPI_BASE}/${randomIndex}`;
      // console.log('Random Pokemon URL:', pokeUrl);
      // this.answered.set(false);

      // this.http.get(pokeUrl).subscribe({
      //   next: (data: any) => {
          
      //     // console.log('Random Pokemon Data:', data);
      //     // let pokemonName = data.name; 
      //     // console.log('Random Pokemon Name:', pokemonName);
      //     // if (pokemonName.includes('-') ) {
      //     //   if (this.arrayOfPokemonWithHyphens.includes(pokemonName)) {
      //     //     const firstIndex = pokemonName.indexOf('-');
      //     //     const secondIndex = pokemonName.indexOf('-', firstIndex + 1);
      //     //     pokemonName = pokemonName.substring(0, secondIndex); // Remove the second hyphen and everything after it
      //     //   }
      //     //   else {
      //     //     pokemonName = pokemonName.substring(0, pokemonName.indexOf('-')); // Remove the hyphen and everything after it
      //     //   }
      //     // }
      //     // this.pokemonInput.set(pokemonName); // Set the input field to the random Pokemon name
      //     // let url = `https://api.pokemontcg.io/v2/cards?q=name:${this.pokemonInput()}`;
      //   },
      //   error: (error) => {
      //     console.error('Error fetching random Pokemon:', error);
      //     reject(false);
      //   }
      // });
      let url = `/api/get-card-data`

      this.http.get(url).subscribe({
        next: (response: any) => {
        console.log(response);
        // this.imageObject = {} // Clear previous images
        // const randomIndex = Math.floor(Math.random() * response.data.length);
        if(response.data.name){
          console.log("Fetching data for ", response.data.name );
        }

        if( response.data && response.data.images && response.data.images.large) {
          //get the price object for the card price and card type
          if( !response.data.tcgplayer || !response.data.tcgplayer.prices || response.data.length === 0) {
            console.log('No prices found for this card or no cards found');
            resolve(false);
            return;
          }
          let priceKeys : any = Object.keys(response.data.tcgplayer.prices); //access price keys as strings in array:'normal', 'holofoil', etc.
          let priceHolder = "N/A";
          let cardTypeHolder = "";
          if(priceKeys.length !== 0) {
            cardTypeHolder = priceKeys[0]; //returns string
            let priceCardType = Object.keys(response.data.tcgplayer.prices[cardTypeHolder]); //returns string array of price card types: 'market', 'low', 'high', etc.
            if(priceCardType.length !== 0) {
              priceHolder = response.data.tcgplayer.prices[cardTypeHolder]['market']; //returns the first price type, Ex: 'market'
              let priceHolderBackup = [];
              priceHolderBackup[0] = response.data.tcgplayer.prices[cardTypeHolder]['directLow']; 
              priceHolderBackup[1] = response.data.tcgplayer.prices[cardTypeHolder]['mid']; 
              
              let i = 0;
              while (priceHolder == null ){
                if (i >= 2){
                  break;
                }
                priceHolder = priceHolderBackup[i];
                i++;
              }
              if (priceHolder == null) {
                console.log('No good prices in ' + cardTypeHolder);
                resolve(false);
                return;
              }
                          
            }
            else{
              console.log('No Prices in ' + cardTypeHolder);
              resolve(false);
              return;
            }
            // console.log('Card Type: ' + cardTypeHolder + ' Price: ' + priceHolder);
          }
          this.imageID++;
          // setPokemonCards
          let setCards : PokemonObject = {
            image: response.data.images.large,
            price: priceHolder,
            cardType: cardTypeHolder
          };

          //loop through the class images object and log the key, image, and price
          // const key = Object.keys(this.imageObject)[0];
          // this.imageObject[this.imageID] = setCards; 
          setInput[this.imageID] = setCards;

          console.log("this.imageID" ,this.imageID );
          console.log("setInput length" , Object.keys(setInput).length );
          // console.log("setInput[this.imageID].image", setInput[this.imageID].image);
          // console.log("setInput[this.imageID].image", setInput[this.imageID].price);
          // setInput.add({[this.imageID] : setCards}); // Add the current imageObject to the set
          resolve(true);
        }
        else{ resolve(true);}
        },
        error: (error) => {
          console.error('Error fetching Pokemon card:', error);
          reject(false);
        }
      });
    });

  }

  resetGame() {
    this.imageObject = {}; // Clear previous images
    this.imageID = 0; // Reset image ID
    this.successfulAdds.set(0); 
    this.score.set(0); 

    this.showPlayState.set(true);
    this.showHowToPlay.set(false);
    // this.answered.set(false);
    this.gameOver.set(false);
  }

  nextCardReset(){
    // this.addImaeObject(this.imageObject);
    this.populatePokemonCardObject();
    // this.answered.set(false);
    this.imageID = Object.keys(this.imageObject).length; // Reset image ID to the current length of the imageObject
    this.answeredCorrect.set(false);
  }

  popimageObject(){
    this.imageObject[1] = this.imageObject[2]; // Shift the second card to the first position
    delete this.imageObject[2]; // Remove the second card
    this.successfulAdds.set(this.successfulAdds() - 1); // Decrease the count of successful adds
  }

  checkAnswer(answer: boolean) {
    const price1 = this.imageObject[1]?.price ?? 0;
    const price2 = this.imageObject[2]?.price ?? 0;

    const hasBothCards : boolean = Boolean(this.imageObject[1] && this.imageObject[2]);

    let obj = {
      price1 : price1,
      price2 : price2,
      hasBothCards : hasBothCards,
      answer : answer

    }
    this.http.post('/api/game-state-user-input', obj).subscribe(
      {
        next: (res : any ) => {
          console.log(res);
          console.log(res.result);
          if (res.result){
            console.log('Answer is correct');
            this.answeredCorrect.set(true);
            this.isSecondCardLoading.set(true);

            this.popimageObject(); // go to next card to compare to
            this.nextCardReset(); // reset the game state for the next card
            this.score.set(this.score() + 1); // Increment score
          }
          else{
            console.log(`Wrong answer | price2: ${price2}, price1: ${price1}`);
            this.answeredCorrect.set(false);
            this.gameOver.set(true); 
            // this.resetGame();

          }
        },

        error : (err) => {
          console.log("error occurred during result logic" + err);
        }

      }
    );

    // const isCorrect = answer ? price2 >= price1 : price2 <= price1;

    // if (hasBothCards && isCorrect) {
    //   console.log('Answer is correct');
    //   this.answeredCorrect.set(true);
    //   this.isSecondCardLoading.set(true);

    //   this.popimageObject(); // go to next card to compare to
    //   this.nextCardReset(); // reset the game state for the next card
    //   this.score.set(this.score() + 1); // Increment score

    // } else {
    //   console.log(`Wrong answer | price2: ${price2}, price1: ${price1}`);
    //   this.answeredCorrect.set(false);
    //   this.gameOver.set(true); 
    // }

  }

  async populatePokemonCardObject(){

    while (this.successfulAdds() < 2) {
      try {
        const result : boolean  = await this.addImageObject(this.imageObject);
        if (result) {
          this.successfulAdds.set(this.successfulAdds() + 1);
        }
      } catch (err) {
        console.error('Error adding image:', err);
      }
    }
    this.showSearchResults.set(true);
    this.showHowToPlay.set(false);
    this.isLoading.set(false);
    this.isSecondCardLoading.set(false);

  }

  playGame(){
    this.isLoading.set(true);
    this.resetGame();
    this.populatePokemonCardObject();
  }

  getPokemonImage(){
    // const inputElement = event.target as HTMLInputElement;
    const sanitized = this.pokemonInput().trim().toLowerCase();
    const encoded = encodeURIComponent(sanitized);

    if (encoded === '') {
      console.log('Input is empty');
      return;
    }
    
    // Fetch token first
    this.http.get<{token: string}>('/api/get-token').subscribe({ //response type is an object, stored in res
      next: (res) => {
        const token = res.token;
        // Call backend to store user input with token
        this.http.post('/api/user-input', { input: encoded, token }).subscribe({
          next: (res) => console.log('User input stored:', res),
          error: (err) => console.error('Failed to store user input:', err)
        });
      },
      error: (err) => {
        console.error('Failed to get token:', err);
      }
    });

    let url = `https://api.pokemontcg.io/v2/cards?q=name:${encoded}`;

    this.http.get(url).subscribe(
      (response: any) => {
      console.log(response);

      // get 3 random cards from the response
      if (response.data.length < 3) {
        console.log('Not enough cards found');
        this.showSearchResults.set(false);
        return;
      }
      const randomIndices = new Set<number>();
      while (randomIndices.size < 3) {
        console.log("response.data.length",response.data.length); // length of pokemon cards in result
        const randomIndex = Math.floor(Math.random() * response.data.length);
        randomIndices.add(randomIndex);
      }
      console.log('Random indices: ', Array.from(randomIndices));
      console.log('Response data length: ', response.data.length);

      this.imageObject = {} // Clear previous images
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
          this.imageObject[id] = {
            image: response.data[i].images.large,
            price: priceHolder,
            cardType: cardTypeHolder
          };

          //loop through the class images object and log the key, image, and price
          // const key = Object.keys(this.imageObject)[i];
          console.log(id + ' ' + this.imageObject[id].image + ' ' + this.imageObject[id].price);
          this.showHowToPlay.set(false);
          this.showSearchResults.set(true);

        }

      }
    })

  }


}
