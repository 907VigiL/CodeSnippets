import numpy as np
import pandas as pd
from collections import OrderedDict
from scipy.stats import binom as binomial
import math
import random


def coin():
    # standard 50/50 coin flipped 100 times and output shows num of heads and tails
    flips = 80
    recordList = []
    for _ in range(flips):
        flip = random.randint(0, 1)
        if (flip == 1):
            recordList.append("H")
        else:
            recordList.append("T")
    # print("Heads:", recordList.count("Heads"))
    # print("Tails:", recordList.count("Tails"))
    return recordList


def weightedCoin():
    # coin set to flip heads 75% of the time flipped 100 times and output shows num of heads and tails
    flips = 80
    weight = 0.75
    recordList = []
    for _ in range(flips):
        turn = np.random.uniform(0, 1)
        # flip = random.triangular(0, 1, 0.75)
        if (turn <= weight):
            recordList.append("H")
        else:
            recordList.append("T")
    # print("Heads:", recordList.count("Heads"))
    # print("Tails:", recordList.count("Tails"))
    return recordList


def generateCoins(numberOfCoins):
    # generates 100 coins and stores their 100 flips in lists
    coins = numberOfCoins
    recordList = []
    typeOfCoinList = []
    for _ in range(coins):
        chooseCoin = random.randint(0, 1)
        if (chooseCoin == 1):
            createdCoin = coin()
            recordList.append(createdCoin)
            typeOfCoinList.append("Normal coin")
        else:
            createdWeightedCoin = weightedCoin()
            recordList.append(createdWeightedCoin)
            typeOfCoinList.append("Weighted coin")
    return recordList, typeOfCoinList


def detectCheater(coinList, typeOfCoinList):
    # check if number of heads is greater then 75% if yes label as cheater
    x = len(coinList)
    coin = 0
    bannedPlayers = 0
    notBannedPlayers = 0
    truePositiveBan = 0
    falsePositiveBan = 0
    cheaterNotCaught = 0
    for _ in range(x):
        if (coinList[coin].count("H") >= 51):
            if (typeOfCoinList[coin] == ("Weighted coin")):
                truePositiveBan += 1
            else:
                falsePositiveBan += 1
            bannedPlayers += 1
            coin += 1
        else:
            if typeOfCoinList[coin] == ("Weighted coin"):
                cheaterNotCaught += 1
            notBannedPlayers += 1
            coin += 1
    print("STAT GENERATED LIST")
    print("Number of Weighted Coins:", typeOfCoinList.count("Weighted coin"))
    print("Number of Normal Coins:", typeOfCoinList.count("Normal coin"))
    print("Number of players Banned:", bannedPlayers)
    print("Number of players not Banned:", notBannedPlayers)
    print("True Positive Bans:", truePositiveBan)
    print("False Positive Bans:", falsePositiveBan)
    print("Cheaters Not Caught:", cheaterNotCaught)


coin_toss_training, coin_list1 = generateCoins(1000)
coin_toss, coin_list2 = generateCoins(1000)

thetaA = 0.5
thetaB = 0.6


def em_training(thetaOld):
    row_prob = []
    # Expectation
    for row in coin_toss_training:
        count_heads = row.count('H')
        # theta here is probabiliy of getting heads
        p_a = binomial.pmf(count_heads, len(row), thetaOld['A'])
        p_b = binomial.pmf(count_heads, len(row), thetaOld['B'])
        p_t = p_a+p_b
        p_a = p_a/p_t  # prob coin is normal coin
        p_b = p_b/p_t  # prob coin is a weighted coin
        row_prob.append(
            {'A': p_a, 'B': p_b, 'count_heads': count_heads, 'total_tosses': len(row)})

    # Maximisation
    new_coin_toss = []
    for row in row_prob:
        total_tosses = row['total_tosses']
        total_heads = row['count_heads']
        A_heads = row['A']*total_heads
        A_tails = row['A']*(total_tosses-total_heads)
        B_heads = row['B']*total_heads
        B_tails = row['B']*(total_tosses-total_heads)
        new_coin_toss.append([A_heads, A_tails, B_heads, B_tails])
    df = pd.DataFrame(new_coin_toss, columns=[
                      'A Heads', 'A Tails', 'B Heads', 'B Tails'])
    new_pa = df['A Heads'].sum()/(df['A Heads'].sum() +
                                  df['A Tails'].sum())  # updates theta values
    new_pb = df['B Heads'].sum()/(df['B Heads'].sum()+df['B Tails'].sum())
    new_theta = OrderedDict({'A': new_pa, 'B': new_pb})
    return new_theta


def antiCheatEm(theta):
    coin = 0
    bannedPlayers = 0
    notBannedPlayers = 0
    truePositiveBan = 0
    falsePositiveBan = 0
    cheaterNotCaught = 0
    for row in coin_toss:
        count_heads = row.count('H')
        # theta here is probabiliy of getting heads
        p_a = binomial.pmf(count_heads, len(row), theta['A'])
        p_b = binomial.pmf(count_heads, len(row), theta['B'])
        p_t = p_a+p_b
        p_a = p_a/p_t  # prob coin is normal coin
        p_b = p_b/p_t  # prob coin is weighted
        # same idea as other anticheat functions but tests prob of coin being an normal or weighted coin
        if (p_a < p_b):
            if (coin_list2[coin] == ("Weighted coin")):
                truePositiveBan += 1
            else:
                falsePositiveBan += 1
            bannedPlayers += 1
            coin += 1
        else:
            if coin_list2[coin] == ("Weighted coin"):
                cheaterNotCaught += 1
            notBannedPlayers += 1
            coin += 1
    print("AI GENERATED LIST")
    print("Number of Weighted Coins:", coin_list2.count("Weighted coin"))
    print("Number of Normal Coins:", coin_list2.count("Normal coin"))
    print("Number of players Banned:", bannedPlayers)
    print("Number of players not Banned:", notBannedPlayers)
    print("True Positive Bans:", truePositiveBan)
    print("False Positive Bans:", falsePositiveBan)
    print("Cheaters Not Caught:", cheaterNotCaught)


theta = OrderedDict({'A': thetaA, 'B': thetaB})

max_iterations = 10000
iterations = 0
diff = 1
tolerance = 1e-6
# runs our training program to find the best vaules of thetaA and thetaB stops once values start repeating
while (iterations < max_iterations) and (diff > tolerance):
    new_theta = em_training(theta)
    diff = math.dist(new_theta.values(), theta.values())
    theta = new_theta
    iterations += 1
    print(new_theta)
# main run of our two funcions
print("####################################################################")
detectCheater(coin_toss, coin_list2)
print("####################################################################")
antiCheatEm(new_theta)
