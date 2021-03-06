from CardTypes import *
from Triggers_Auras import *

from numpy.random import choice as npchoice
from numpy.random import randint as nprandint

def fixedList(listObj):
	return listObj[0:len(listObj)]
	
def PRINT(game, string, *args):
	if game.GUI:
		if not game.mode: game.GUI.printInfo(string)
	elif not game.mode: print("game's guide mode is 0\n", string)
	
def classforDiscover(initiator):
	Class = initiator.Game.heroes[initiator.ID].Class
	if Class != "Neutral": return Class #如果发现的发起者的职业不是中立，则返回那个职业
	elif initiator.Class != "Neutral": return initiator.Class #如果玩家职业是中立，但卡牌职业不是中立，则发现以那个卡牌的职业进行
	else: return npchoice(initiator.Game.Classes) #如果玩家职业和卡牌职业都是中立，则随机选取一个职业进行发现。
	
	
class BoomBot(Minion):
	Class, race, name = "Neutral", "Mech", "Boom Bot"
	mana, attack, health = 1, 1, 1
	index = "GVG~Neutral~Minion~1~1~1~Mech~Boom Bot~Deathrattle~Uncollectible"
	requireTarget, keyWord, description = False, "", "Deathrattle: Deal 1~4 damage to a random enemy"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [Deal1to4DamagetoaRandomEnemy(self)]
		
class Deal1to4DamagetoaRandomEnemy(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			enemy = None
			PRINT(curGame, "Deathrattle: Deal 1~4 damage to a random enemy triggers.")
			if curGame.guides:
				i, where, damage = curGame.guides.pop(0)
				if where: enemy = curGame.find(i, where)
			else:
				targets = curGame.charsAlive(3-self.entity.ID)
				if targets:
					enemy, damage = npchoice(targets), nprandint(1, 5)
					curGame.fixedGuides.append((enemy.position, enemy.type+str(enemy.ID), damage))
				else:
					curGame.fixedGuides.append((0, '', 0))
			if enemy:
				self.entity.dealsDamage(enemy, damage)
				
				

class GoldenKobold(Minion):
	Class, race, name = "Neutral", "", "Golden Kobold"
	mana, attack, health = 3, 6, 6
	index = "Kobolds~Neutral~Minion~3~6~6~None~Golden Kobold~Taunt~Battlecry~Legendary~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: Replace your hand with Legendary minions"
	poolIdentifier = "Legendary Minions"
	@classmethod
	def generatePool(cls, Game):
		return "Legendary Minions", list(Game.LegendaryMinions.values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Golden Kobold's battlecry replaces player's hand with Legendary minions")
			if curGame.guides:
				hand = curGame.guides.pop(0)
			else:
				hand = tuple(npchoice(self.rngPool("Legendary Minions"), len(curGame.Hand_Deck.hands[self.ID]), replace=True))
				curGame.fixedGuides.append(hand)
			if hand:
				curGame.Hand_Deck.extractfromHand(None, self.ID, all=True)
				curGame.Hand_Deck.addCardtoHand(hand, self.ID, "type")
		return None
		
class TolinsGoblet(Spell):
	Class, name = "Neutral", "Tolin's Goblet"
	requireTarget, mana = False, 3
	index = "Kobolds~Neutral~Spell~3~Tolin's Goblet~Uncollectible"
	description = "Draw a card. Fill your hand with copies of it"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Tolin's Goblet lets player draw a card and fills their hand with copies of it")
		card, mana = self.Game.Hand_Deck.drawCard(self.ID)
		if card and self.Game.Hand_Deck.handNotFull(self.ID):
			copies = [card.selfCopy(self.ID) for i in range(self.Game.Hand_Deck.spaceinHand(self.ID))]
			self.Game.Hand_Deck.addCardtoHand(copies, self.ID)
		return None
		
class WondrousWand(Spell):
	Class, name = "Neutral", "Wondrous Wand"
	requireTarget, mana = False, 3
	index = "Kobolds~Neutral~Spell~3~Wondrous Wand~Uncollectible"
	description = "Draw 3 cards. Reduce their costs to (0)"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "WondrousWand lets player draw 3 cards and reduces their costs to (0)")
		for i in range(3):
			card, mana = self.Game.Hand_Deck.drawCard(self.ID)
			if card:
				ManaMod(card, changeby=0, changeto=0).applies()
				self.Game.Manas.calcMana_Single(card)
		return None
		
class ZarogsCrown(Spell):
	Class, name = "Neutral", "Zarog's Crown"
	requireTarget, mana = False, 3
	index = "Kobolds~Neutral~Spell~3~Zarog's Crown~Uncollectible"
	description = "Discover a Legendary minion. Summon two copies of it"
	poolIdentifier = "Legendary Minions as Druid to Summon"
	@classmethod
	def generatePool(cls, Game):
		classCards = {s : [value for key, value in Game.ClassCards[s].items() if "~Minion~" in key and "~Legendary" in key] for s in Game.Classes}
		classCards["Neutral"] = [value for key, value in Game.NeutralCards.items() if "~Minion~" in key and "~Legendary" in key]
		return ["Legendary Minions as %s to Summon"%Class for Class in Game.Classes], \
			[classCards[Class]+classCards["Neutral"] for Class in Game.Classes]
			
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.space(self.ID):
			if curGame.mode == 0:
				if curGame.guides:
					minion = curGame.guides.pop(0)
				else:
					key = "Legendary Minions as %s to Summon"%classforDiscover(self)
					if self.ID != curGame.turn or "byOthers" in comment:
						minion = npchoice(self.rngPool(key))
						curGame.fixedGuides.append(minion)
						PRINT(curGame, "Zarog's Crown summons two copies of a random Legendary minion")
						curGame.summon([minion(self.Game, self.ID) for i in range(2)], (-1, "totheRightEnd"), self.ID)
					else:
						PRINT(curGame, "Zarog's Crown lets playersummons two copies of a random Legendary minion")
						minions = npchoice(self.rngPool(key), 3, replace=False)
						curGame.options = [minion(curGame, self.ID) for minion in minions]
						curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.summon([option, type(option)(self.Game, self.ID)], (-1, "totheRightEnd"), self.ID)
		


class Bomb(Spell):
	Class, name = "Neutral", "Bomb"
	requireTarget, mana = False, 5
	index = "Boomsday~Neutral~Spell~5~Bomb~Casts When Drawn~Uncollectible"
	description = "Casts When Drawn. Deal 5 damage to your hero"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		damage = (5 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
		PRINT(self.Game, "Bomb is cast and deals %d damage to player."%damage)
		self.dealsDamage(self.Game.heroes[self.ID], damage)
		return None


class EtherealLackey(Minion):
	Class, race, name = "Neutral", "", "Ethereal Lackey"
	mana, attack, health = 1, 1, 1
	index = "Shadows~Neutral~Minion~1~1~1~None~Ethereal Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = False, "", "Battlecry: Discover a spell"
	poolIdentifier = "Druid Spells"

	@classmethod
	def generatePool(cls, Game):
		return [Class + " Spells" for Class in Game.Classes], \
			   [[value for key, value in Game.ClassCards[Class].items() if "~Spell~" in key] for Class in Game.Classes]

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					PRINT(curGame, "Ethereal Lackey's battlecry adds a spell to player's hand")
					curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
				else:
					key = classforDiscover(self) + " Spells"
					if "byOthers" in comment:
						spell = npchoice(self.rngPool(key))
						curGame.fixedGuides.append(spell)
						PRINT(curGame, "Ethereal Lackey's battlecry adds a random spell to player's hand")
						curGame.Hand_Deck.addCardtoHand(spell, self.ID, "type", byDiscover=True)
					else:
						spells = npchoice(self.rngPool(key), 3, replace=False)
						curGame.options = [spell(curGame, self.ID) for spell in spells]
						PRINT(curGame, "Ethereal Lackey's battlecry lets player discover a spell")
						curGame.Discover.startDiscover(self)
		return None

	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)


class FacelessLackey(Minion):
	Class, race, name = "Neutral", "", "Faceless Lackey"
	mana, attack, health = 1, 1, 1
	index = "Shadows~Neutral~Minion~1~1~1~None~Faceless Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon a 2-Cost minion"
	poolIdentifier = "2-Cost Minions to Summon"

	@classmethod
	def generatePool(cls, Game):
		return "2-Cost Minions to Summon", list(Game.MinionsofCost[2].values())

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(self.rngPool("2-Cost Minions to Summon"))
				curGame.fixedGuides.append(minion)
			PRINT(curGame, "Faceless Lackey's battlecry summons a random 2-Cost minions.")
			curGame.summon(minion(curGame, self.ID), self.position + 1, self.ID)
		return None


class GoblinLackey(Minion):
	Class, race, name = "Neutral", "", "Goblin Lackey"
	mana, attack, health = 1, 1, 1
	index = "Shadows~Neutral~Minion~1~1~1~None~Goblin Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = True, "", "Battlecry: Give a friendly minion +1 Attack and Rush"

	def targetExists(self, choice=0):
		return self.selectableFriendlyMinionExists()

	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.ID == self.ID and target != self and target.onBoard

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Goblin Lackey's battlecry gives friendly minion %s +2 attack and Rush." % target.name)
			target.buffDebuff(1, 0)
			target.getsKeyword("Rush")
		return target


class KoboldLackey(Minion):
	Class, race, name = "Neutral", "", "Kobold Lackey"
	mana, attack, health = 1, 1, 1
	index = "Shadows~Neutral~Minion~1~1~1~None~Kobold Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = True, "", "Battlecry: Deal 2 damage"

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Kobold Lackey's battlecry deals 2 damage to %s" % target.name)
			self.dealsDamage(target, 2)
		return target


class WitchyLackey(Minion):
	Class, race, name = "Neutral", "", "Witchy Lackey"
	mana, attack, health = 1, 1, 1
	index = "Shadows~Neutral~Minion~1~1~1~None~Witchy Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = True, "", "Battlecry: Transform a friendly minion into one that costs (1) more"
	poolIdentifier = "1-Cost Minions to Summon"

	@classmethod
	def generatePool(cls, Game):
		return ["%d-Cost Minions to Summon" % cost for cost in Game.MinionsofCost], \
			   [list(Game.MinionsofCost[cost].values()) for cost in Game.MinionsofCost]

	def targetExists(self, choice=0):
		return self.selectableFriendlyMinionExists()

	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.ID == self.ID and target != self and target.onBoard

	# 不知道如果目标随从被返回我方手牌会有什么结算，可能是在手牌中被进化
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			curGame = self.Game
			PRINT(curGame, "Witchy Lackey's battlecry transforms friendly minion %s into one that costs 1 more." % target.name)
			if curGame.mode == 0:
				if curGame.guides:
					newMinion = curGame.guides.pop(0)
				else:
					cost = type(target).mana + 1
					while cost not in curGame.MinionsofCost:
						cost -= 1
					newMinion = npchoice(self.rngPool("%d-Cost Minions to Summon" % cost))
					curGame.fixedGuides.append(newMinion)
			newMinion = newMinion(curGame, target.ID)
			curGame.transform(target, newMinion)
			target = newMinion
		return target


class TitanicLackey(Minion):
	Class, race, name = "Neutral", "", "Titanic Lackey"
	mana, attack, health = 1, 1, 1
	index = "Uldum~Neutral~Minion~1~1~1~None~Titanic Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = True, "", "Battlecry: Give a friendly minion +2 Health"

	def targetExists(self, choice=0):
		return self.selectableFriendlyMinionExists(choice)

	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.ID == self.ID and target != self and target.onBoard

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Titanic Lackey's battlecry gives friendly minion %s +2 Health and Taunt" % target.name)
			target.buffDebuff(0, 2)
			target.getsKeyword("Taunt")
		return target


class DraconicLackey(Minion):
	Class, race, name = "Neutral", "", "Draconic Lackey"
	mana, attack, health = 1, 1, 1
	index = "Dragons~Neutral~Minion~1~1~1~None~Draconic Lackey~Battlecry~Uncollectible"
	requireTarget, keyWord, description = False, "", "Battlecry: Discover a Dragon"
	poolIdentifier = "Dragons as Druid"

	@classmethod
	def generatePool(cls, Game):
		classCards = {s: [] for s in Game.ClassesandNeutral}
		for key, value in Game.MinionswithRace["Dragon"].items():
			classCards[key.split('~')[1]].append(value)
		return ["Dragons as " + Class for Class in Game.Classes], \
			   [classCards[Class] + classCards["Neutral"] for Class in Game.Classes]

	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					PRINT(curGame, "Draconic Lackey's battlecry adds a Dragon to player's hand")
					curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
				else:
					key = "Dragons as " + classforDiscover(self)
					if "byOthers" in comment:
						dragon = npchoice(self.rngPool(key))
						curGame.fixedGuides.append(dragon)
						PRINT(curGame, "Draconic Lackey's battlecry adds a random Dragon to player's hand")
						curGame.Hand_Deck.addCardtoHand(dragon, self.ID, "type", byDiscover=True)
					else:
						dragons = npchoice(self.rngPool(key), 3, replace=False)
						curGame.options = [dragon(curGame, self.ID) for dragon in dragons]
						PRINT(curGame, "Draconic Lackey's battlecry lets player discover a Dragon")
						curGame.Discover.startDiscover(self)
		return None

	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)

Lackeys = [DraconicLackey, EtherealLackey, FacelessLackey, GoblinLackey, KoboldLackey, TitanicLackey, WitchyLackey]

AcrossPacks_Indices = {"GVG~Neutral~Minion~1~1~1~Mech~Boom Bot~Deathrattle~Uncollectible": BoomBot,
					"Kobolds~Neutral~Minion~3~6~6~None~Golden Kobold~Taunt~Battlecry~Legendary~Uncollectible": GoldenKobold,
					"Kobolds~Neutral~Spell~3~Tolin's Goblet~Uncollectible": TolinsGoblet,
					"Kobolds~Neutral~Spell~3~Wondrous Wand~Uncollectible": WondrousWand,
					"Kobolds~Neutral~Spell~3~Zarog's Crown~Uncollectible": ZarogsCrown,
					"Boomsday~Neutral~Spell~5~Bomb~Casts When Drawn~Uncollectible": Bomb,

					"Shadows~Neutral~Minion~1~1~1~None~Ethereal Lackey~Battlecry~Uncollectible":EtherealLackey,
					"Shadows~Neutral~Minion~1~1~1~None~Faceless Lackey~Battlecry~Uncollectible": FacelessLackey,
					"Shadows~Neutral~Minion~1~1~1~None~Goblin Lackey~Battlecry~Uncollectible": GoblinLackey,
					"Shadows~Neutral~Minion~1~1~1~None~Kobold Lackey~Battlecry~Uncollectible": KoboldLackey,
					"Shadows~Neutral~Minion~1~1~1~None~Witchy Lackey~Battlecry~Uncollectible": WitchyLackey,
					"Uldum~Neutral~Minion~1~1~1~None~Titanic Lackey~Battlecry~Uncollectible": TitanicLackey,
					"Dragons~Neutral~Minion~1~1~1~None~Draconic Lackey~Battlecry~Uncollectible": DraconicLackey,
					}
