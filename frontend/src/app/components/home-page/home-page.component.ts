import { CurrencyPipe, KeyValuePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, signal } from '@angular/core';

interface PokemonObject {
  image: string;
  price?: number | string;
  cardType?: string;
}

@Component({
  selector: 'app-home-page',
  imports: [KeyValuePipe, CurrencyPipe],
  templateUrl: './home-page.component.html',
  styleUrl: './home-page.component.css'
})
export class HomePageComponent {

  constructor(private http: HttpClient) {}

  showHowToPlay       = signal<boolean>(false);
  showSearchResults   = signal<boolean>(false);
  showPlayState       = signal<boolean>(false);
  pokemonInput        = signal<string>('');
  imageID             : number = 0;
  answered            = signal<boolean>(false);
  answeredCorrect     = signal<boolean>(false);
  gameOver            = signal<boolean>(false);
  successfulAdds      = signal<number>(0);
  score               = signal<number>(0);
  isLoadingCards      = signal<boolean>(false);
  isSecondCardLoading = signal<boolean>(false);
  playStartedAt       = signal<string>('');

  // ── Session token — fetched on Play, cleared after submit ─────────────────
  private gameSessionToken: string | null = null;

  arrayOfPokemonWithHyphens: string[] = [
    'Ho-Oh', 'Porygon-Z', 'Jangmo-o', 'Hakamo-o', 'Kommo-o',
    'Ting-Lu', 'Chien-Pao', 'Wo-Chien', 'Chi-Yu'
  ];

  imageObject: { [key: string | number]: PokemonObject } = {};
  gameStateCompareSet: Set<{ [key: number]: PokemonObject }> = new Set();

  getImagesLength() {
    return Object.keys(this.imageObject).length;
  }

  // ── Token fetch — called once when Play is clicked ────────────────────────
  private fetchGameSessionToken(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.http.get<{ token: string }>('/api/game-session/token', {
        withCredentials: true  // sends Flask session cookie so backend can store token in session
      }).subscribe({
        next: (res) => {
          this.gameSessionToken = res.token;
          resolve();
        },
        error: (err) => {
          console.error('Failed to fetch game session token:', err);
          reject(err);
        }
      });
    });
  }

  // ── Submit on Game Over ───────────────────────────────────────────────────
  private submitSession(finalScore: number): void {
    if (!this.gameSessionToken) {
      console.error('No session token available — cannot submit session.');
      return;
    }
    if (!this.playStartedAt()) {
      console.error('No start time recorded — cannot submit session.');
      return;
    }

    this.http.post('/api/game-session', {
      play_started_at: this.playStartedAt(),  // string value from signal
      final_score:     finalScore,
      token:           this.gameSessionToken,
    }, {
      withCredentials: true  // sends Flask session cookie for token validation
    }).subscribe({
      next: (res) => {
        console.log('Game session stored:', res);
        this.gameSessionToken = null;  // clear after successful submit — one-time use
      },
      error: (err) => {
        console.error('Failed to store game session:', err);
      }
    });
  }

  // ── Play — fetch token + record start time ────────────────────────────────
  async playGame() {
    this.isLoadingCards.set(true);
    this.resetGame();

    try {
      // Both happen before the game starts: record time and fetch token in parallel
      const [_, __] = await Promise.all([
        this.fetchGameSessionToken(),
        this.populatePokemonCardObject()
      ]);
      this.playStartedAt.set(new Date().toISOString());
    } catch (err) {
      console.error('Error starting game:', err);
      this.isLoadingCards.set(false);
    }
  }

  // ── Answer check ──────────────────────────────────────────────────────────
  checkAnswer(answer: boolean) {
    const price1 = this.imageObject[1]?.price ?? 0;
    const price2 = this.imageObject[2]?.price ?? 0;
    const hasBothCards = Boolean(this.imageObject[1] && this.imageObject[2]);

    this.http.post('/api/game-state-check-answer', {
      price1, price2, hasBothCards, answer
    }).subscribe({
      next: (res: any) => {
        if (res.result) {
          console.log('Answer is correct');
          this.answeredCorrect.set(true);
          this.isSecondCardLoading.set(true);
          this.popimageObject();
          this.nextCardReset();
          this.score.set(this.score() + 1);
        } else {
          console.log(`Wrong answer | price1: ${price1}, price2: ${price2}`);
          this.answeredCorrect.set(false);
          this.gameOver.set(true);
          this.submitSession(this.score());  // ← .() to get signal value, not the signal itself
        }
      },
      error: (err) => {
        console.error('Error during answer check:', err);
      }
    });
  }

  resetGame() {
    this.imageObject = {};
    this.imageID = 0;
    this.successfulAdds.set(0);
    this.score.set(0);
    this.showPlayState.set(true);
    this.showHowToPlay.set(false);
    this.gameOver.set(false);
    this.gameSessionToken = null;  // clear any leftover token from a previous game
  }

  nextCardReset() {
    this.populatePokemonCardObject();
    this.imageID = Object.keys(this.imageObject).length;
    this.answeredCorrect.set(false);
  }

  popimageObject() {
    this.imageObject[1] = this.imageObject[2];
    delete this.imageObject[2];
    this.successfulAdds.set(this.successfulAdds() - 1);
  }

  async populatePokemonCardObject() {
    while (this.successfulAdds() < 2) {
      try {
        const result: boolean = await this.addImageObject(this.imageObject);
        if (result) {
          this.successfulAdds.set(this.successfulAdds() + 1);
        }
      } catch (err) {
        console.error('Error adding image:', err);
      }
    }
    this.showSearchResults.set(true);
    this.showHowToPlay.set(false);
    this.isLoadingCards.set(false);
    this.isSecondCardLoading.set(false);
  }

  addImageObject(setInput: { [key: number]: PokemonObject }): Promise<boolean> {
    return new Promise((resolve, reject) => {
      this.http.get('/api/get-card-data').subscribe({
        next: (response: any) => {
          if (response.data?.name) {
            console.log('Fetching data for', response.data.name);
          }
          if (response.data?.images?.large) {
            if (!response.data.tcgplayer?.prices) {
              console.log('No prices found');
              resolve(false);
              return;
            }
            const priceKeys: string[] = Object.keys(response.data.tcgplayer.prices);
            if (priceKeys.length === 0) { resolve(false); return; }

            const cardTypeHolder = priceKeys[0];
            const priceData = response.data.tcgplayer.prices[cardTypeHolder];
            let priceHolder: number | null =
              priceData['market'] ?? priceData['directLow'] ?? priceData['mid'] ?? null;

            if (priceHolder == null) {
              console.log('No usable price in', cardTypeHolder);
              resolve(false);
              return;
            }

            this.imageID++;
            setInput[this.imageID] = {
              image:    response.data.images.large,
              price:    priceHolder,
              cardType: cardTypeHolder
            };
            resolve(true);
          } else {
            resolve(true);
          }
        },
        error: (err) => {
          console.error('Error fetching Pokemon card:', err);
          reject(false);
        }
      });
    });
  }

  getPokemonImage() {
    const sanitized = this.pokemonInput().trim().toLowerCase();
    const encoded = encodeURIComponent(sanitized);
    if (!encoded) { console.log('Input is empty'); return; }

    this.http.get<{ token: string }>('/api/get-token').subscribe({
      next: (res) => {
        this.http.post('/api/user-input', { input: encoded, token: res.token }).subscribe({
          next: (res) => console.log('User input stored:', res),
          error: (err) => console.error('Failed to store user input:', err)
        });
      },
      error: (err) => console.error('Failed to get token:', err)
    });

    this.http.get(`https://api.pokemontcg.io/v2/cards?q=name:${encoded}`).subscribe({
      next: (response: any) => {
        if (response.data.length < 3) { this.showSearchResults.set(false); return; }

        const randomIndices = new Set<number>();
        while (randomIndices.size < 3) {
          randomIndices.add(Math.floor(Math.random() * response.data.length));
        }

        this.imageObject = {};
        for (const i of randomIndices) {
          const card = response.data[i];
          if (!card?.images?.large) continue;

          const priceKeys: string[] = Object.keys(card.tcgplayer?.prices ?? {});
          let priceHolder: any = 'N/A';
          let cardTypeHolder = '';

          if (priceKeys.length) {
            cardTypeHolder = priceKeys[0];
            const priceTypes = Object.keys(card.tcgplayer.prices[cardTypeHolder]);
            if (priceTypes.length) {
              priceHolder = card.tcgplayer.prices[cardTypeHolder][priceTypes[0]];
            }
          }

          const id = crypto.randomUUID();
          this.imageObject[id] = { image: card.images.large, price: priceHolder, cardType: cardTypeHolder };
          this.showHowToPlay.set(false);
          this.showSearchResults.set(true);
        }
      }
    });
  }
}