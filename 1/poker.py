#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------

from itertools import combinations
from functools import reduce


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему
    """
    
    cards_val = {"2": 2, "3": 3, "4": 4, 
                 "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,  
                 "10": 10, "T": 10,"J": 11, "Q": 12,  
                 "K": 13, "A": 14,}
    
    return sorted([cards_val[i[:-1]] for i in hand], reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    
    return len({i[1] for i in hand}) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги 
    формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)
    """
    
    return all(map(lambda x: x == 1, 
                   [s - t for s, t in zip(ranks, ranks[1:])]))


def kind(n, ranks):
    """Возвращает наибольший ранг, который n раз 
    встречается в данной руке.
    Возвращает None, если ничего не найдено
    """
    
    res = None
    counter_ = {x: ranks.count(x) for x in ranks if ranks.count(x) == n}
    if len(counter_) > 0:        
        res = reduce(lambda x, y: x if x > y else y, counter_)
    
    return res if res else None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None
    """
    
    counter_ = {x: ranks.count(x) for x in ranks if ranks.count(x) == 2}
    
    res = None
    
    if len(counter_) == 2:
        res = tuple(counter_.keys())
    
    return res


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    
    return max(combinations(hand, 5), key=hand_rank)


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    
    cards_ranks = {"2", "3", "4", "5", "6", "7", "8", "9", "T","J", "Q", "K", "A"} 
    # Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
    black_suits = { "C", "S"}
    red_suits = {"H", "D"}
    res = x = y = None
    
    
    if ("?B" in hand) & ("?R" in hand):
        # убираем джокеров, на их место будем добавлять карты перебором
        hand.remove("?B")
        hand.remove("?R")
               
        res = reduce(
            # размеры вычислений малы, можно в более короткой записи
            # лямбда сворачивает список всех "рук" через определение
            # "руки" большего ранга
            lambda x, y: 
            x if hand_rank(x) > hand_rank(y) else y,            
            # перебираем все возможные комбинации карт для двух джокеров
            [best_hand(hand + [i] + [j]) 
             for i in [rb + sb for rb in cards_ranks for sb in black_suits] if i not in hand
             for j in [rd + sd for rd in cards_ranks for sd in red_suits] if j not in hand])        
        
        
    elif "?B" in hand:
        hand.remove("?B")
        
        res = reduce(lambda x,y: 
            x if hand_rank(x)[0] > hand_rank(y)[0] else
            x if (hand_rank(x)[0] == hand_rank(y)[0]) & (hand_rank(x) > hand_rank(y)) else
            y,
            [best_hand(hand + [i]) for i in [r+s for r in cards_ranks for s in black_suits]
            if i not in hand])
        
    elif "?R" in hand:
        hand.remove("?R")
        
        res = reduce(lambda x,y: 
            x if hand_rank(x)[0] > hand_rank(y)[0] else
            x if (hand_rank(x)[0] == hand_rank(y)[0]) & (hand_rank(x) > hand_rank(y)) else
            y,
            [best_hand(hand + [i]) for i in [r+s for r in cards_ranks for s in red_suits]
            if i not in hand])
    else:
        res = best_hand(hand)
    
    return res


def test_best_hand():
    print ("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    assert (sorted(best_hand("6C 7C 8C 9C TC JC AC".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])    
    print ('OK')


def test_best_wild_hand():
    print ("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print ('OK')

if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
    #print(card_ranks(['10C', '2C', '3C', '3H', '7D']))
    #print(kind(2, card_ranks(['3C', '3C', '10C', '5H', '5D'])))
    pass
