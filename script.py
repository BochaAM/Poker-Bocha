import pygame
import random
import os
import sys

SUITS = ["H", "D", "C", "S"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
START_CHIPS = 1000
CARD_WIDTH, CARD_HEIGHT = 85, 125

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    def to_str(self):
        return f"{RANKS[self.rank]}{SUITS[self.suit]}"

class Player:
    def __init__(self, name, ptype):
        self.name = name
        self.type = ptype
        self.hand = []
        self.folded = False
        self.chips = START_CHIPS
        self.current_bet = 0

def load_card_images():
    images = {}
    for suit in SUITS:
        for rank in RANKS:
            fname = os.path.join("images", f"{rank}{suit}.png")
            img = pygame.image.load(fname).convert()
            images[f"{rank}{suit}"] = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
    back = pygame.image.load(os.path.join("images", "back.png")).convert()
    images["back"] = pygame.transform.scale(back, (CARD_WIDTH, CARD_HEIGHT))
    return images

def create_deck():
    deck = []
    for s in range(4):
        for r in range(13):
            deck.append(Card(r, s))
    random.shuffle(deck)
    return deck

def deal_to_players(players, deck):
    for p in players:
        p.hand = [deck.pop(), deck.pop()]
        p.folded = False
        p.current_bet = 0

def community_cards(deck, n):
    return [deck.pop() for _ in range(n)]

def draw_text(surf, text, font, color, pos, center=False):
    s = font.render(text, True, color)
    rect = s.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surf.blit(s, rect)

def draw_card(surf, card, images, pos, show=True):
    if show:
        surf.blit(images[card.to_str()], pos)
    else:
        surf.blit(images["back"], pos)

def draw_button(surf, rect, text, font, color, bgcolor):
    pygame.draw.rect(surf, bgcolor, rect)
    pygame.draw.rect(surf, (255,255,255), rect, 2)
    s = font.render(text, True, color)
    s_rect = s.get_rect(center=rect.center)
    surf.blit(s, s_rect)

def betting_round(screen, font, card_images, players, player_idx, pot, min_bet, community, show_community, stage):
    highest_bet = min_bet
    any_raise = False
    for p in players: p.current_bet = 0

    order = list(range(player_idx, len(players))) + list(range(0, player_idx))
    betting = True
    while betting:
        betting = False
        for idx in order:
            p = players[idx]
            if p.folded or p.chips == 0:
                continue
            to_call = highest_bet - p.current_bet
            bet = 0
            if p.type == 0:
                action = None
                while action is None:
                    draw_full_table(screen, card_images, players, community, pot, font, show_community, stage, to_call)
                    # Кнопки: слева Fold/Call, справа Raise/All-in
                    y_btn = 670
                    btns = [
                        ("Fold", pygame.Rect(180, y_btn, 120, 45)),
                        ("Call", pygame.Rect(320, y_btn, 120, 45)),
                        ("Raise", pygame.Rect(760, y_btn, 120, 45)),
                        ("All-in", pygame.Rect(900, y_btn, 120, 45))
                    ]
                    for name, rect in btns:
                        draw_button(screen, rect, name, font, (0,0,0), (255,255,128) if name!="Fold" else (240,160,160))
                    pygame.display.flip()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            mx, my = pygame.mouse.get_pos()
                            for name, rect in btns:
                                if rect.collidepoint(mx, my):
                                    action = name
                                    break
                    pygame.time.wait(40)
                if action == "Fold":
                    p.folded = True
                    continue
                elif action == "All-in" or to_call >= p.chips:
                    bet = p.chips
                elif action == "Raise":
                    bet = min(p.chips, to_call + 50)
                    highest_bet = p.current_bet + bet
                    any_raise = True
                else:
                    bet = min(p.chips, to_call)
            else:
                if p.type == 1 and not any_raise and p.chips > to_call + 30:
                    bet = min(p.chips, to_call + 30 + random.randint(0,50))
                    highest_bet = p.current_bet + bet
                    any_raise = True
                elif p.type == 2 and to_call > p.chips // 2:
                    p.folded = True
                    continue
                elif p.type == 2 and to_call < p.chips // 8:
                    bet = min(p.chips, to_call)
                elif p.type == 3 and random.randint(0,3)==0:
                    p.folded = True
                    continue
                else:
                    bet = min(p.chips, to_call)
            p.chips -= bet
            p.current_bet += bet
            pot += bet
            if p.current_bet > highest_bet: highest_bet = p.current_bet
            if bet > to_call: betting = True
    return pot

def draw_full_table(screen, card_images, players, community, pot, font, show_all, stage, to_call=0):
    screen.fill((0, 100, 0))
    w, h = screen.get_size()
    # --- Community ---
    for i, c in enumerate(community):
        show = True if show_all else (stage=="showdown")
        draw_card(screen, c, card_images, (w//2-110+100*i, h//2-60), True)
    draw_text(screen, f"Pot: {pot}", font, (255,255,255), (w//2, h//2+80), center=True)

    # --- Игроки ---
    # Ты (внизу)
    # Info строка теперь только под картами!
    # Карты игрока
    for i, c in enumerate(players[0].hand):
        draw_card(screen, c, card_images, (w//2-70+110*i, h-170), True)
    draw_text(screen, f"You ({players[0].chips})", font, (255,255,255), (w//2, h-30), center=True)
    # Info ("Your chips", "Pot", "To call") -- выше карт
    draw_text(screen, f"Your chips: {players[0].chips}   Pot: {pot}   To call: {to_call}", font, (255,255,255), (w//2, h-210), center=True)

    # Левый бот
    draw_text(screen, f"{players[1].name} ({players[1].chips})", font, (255,255,255), (60, h//2-80))
    for i, c in enumerate(players[1].hand):
        draw_card(screen, c, card_images, (50+95*i, h//2-30), show_all or (players[1].type==0))
    # Верхний бот
    draw_text(screen, f"{players[2].name} ({players[2].chips})", font, (255,255,255), (w//2, 45), center=True)
    for i, c in enumerate(players[2].hand):
        draw_card(screen, c, card_images, (w//2-70+110*i, 80), show_all or (players[2].type==0))
    # Правый бот
    draw_text(screen, f"{players[3].name} ({players[3].chips})", font, (255,255,255), (w-340, h//2-80))
    for i, c in enumerate(players[3].hand):
        draw_card(screen, c, card_images, (w-200+95*i, h//2-30), show_all or (players[3].type==0))
    pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Texas Hold'em Poker (pygame)")
    font = pygame.font.Font(None, 40)
    card_images = load_card_images()
    players = [Player("You", 0), Player("Bot Aggressive", 1), Player("Bot Cautious", 2), Player("Bot Random", 3)]

    running = True
    while running:
        deck = create_deck()
        deal_to_players(players, deck)
        community = []
        pot = 0

        # Префлоп
        pot = betting_round(screen, font, card_images, players, 0, pot, 10, community, False, "preflop")
        # Флоп
        community += community_cards(deck, 3)
        pot = betting_round(screen, font, card_images, players, 0, pot, 0, community, False, "flop")
        # Тёрн
        community += community_cards(deck, 1)
        pot = betting_round(screen, font, card_images, players, 0, pot, 0, community, False, "turn")
        # Ривер
        community += community_cards(deck, 1)
        pot = betting_round(screen, font, card_images, players, 0, pot, 0, community, False, "river")

        # Шоудаун
        draw_full_table(screen, card_images, players, community, pot, font, True, "showdown")
        pygame.time.wait(500)
        alive = [i for i,p in enumerate(players) if not p.folded]
        if alive:
            winner = random.choice(alive)
            players[winner].chips += pot
            msg = f"Winner: {players[winner].name}! +{pot} chips"
        else:
            msg = "Everyone folded!"
        draw_text(screen, msg, font, (255,255,0), (screen.get_width()//2, 50), center=True)
        pygame.display.flip()
        pygame.time.wait(2200)

        waiting = True
        while waiting:
            draw_text(screen, "Play again? (Y/N)", font, (255,255,255), (screen.get_width()//2, 600), center=True)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        return
                    if event.key == pygame.K_y:
                        waiting = False
            pygame.time.wait(100)

if __name__ == "__main__":
    main()
