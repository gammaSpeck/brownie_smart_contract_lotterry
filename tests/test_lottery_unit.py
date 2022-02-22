from brownie import network, exceptions
from scripts.utils import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest

# 0.0172 at the moment of testing
# 17_0000000000_000000 => 18 decimal places
# def test_get_entrance_fee():
#     account = get_account()
#     price_feed_address = get_price_feed_address()
#     lottery = Lottery.deploy(price_feed_address, {"from": account})
#     entrance_fee = lottery.getEntranceFee()
#     assert entrance_fee > Web3.toWei(0.016, "ether")
#     assert entrance_fee < Web3.toWei(0.022, "ether")


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    # Act
    # 200 usd per 1 eth
    # usd entryFee is $50
    # 2000/1 = 50/x ===> x = 50/2000 =>
    # x = 0.025
    entrance_fee = lottery.getEntranceFee()
    # Assert
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(AttributeError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1000})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1000})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # Position 2 => CALCULATING_WINNER
    assert lottery.currentLotteryState() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})

    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})

    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})

    requestId = transaction.events["RequestedRandomness"]["requestId"]
    # Here we are mocking the Chain link Node's callback
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        requestId, STATIC_RNG, lottery.address, {"from": account}
    )
    starting_bal_of_account = account.balance()
    bal_of_lottery = lottery.balance()
    # 777 % 3 = 0 => 0th Index => account is winner
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_bal_of_account + bal_of_lottery
