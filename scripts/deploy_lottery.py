from brownie import Lottery, config, network
from scripts.utils import fund_with_link, get_account, get_contract
import time


def deploy_lottery():
    account = get_account()
    active_network = network.show_active()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][active_network]["fee"],
        config["networks"][active_network]["keyhash"],
        {"from": account},
        publish_source=config["networks"][active_network].get("verify", False),
    )

    print("Deployed Lottery!!!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("Lottery has started!!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 10000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # Fund the contract
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the latest winner!!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
