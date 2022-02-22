from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)


DECIMALS = 8
STARTING_PRICE = 2000 * 10**8

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]


def get_account(index=0, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)

    active_network = network.show_active()
    if (
        active_network in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or active_network in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


def deploy_mocks(decimals=DECIMALS, initial_value=STARTING_PRICE):
    print("Deploying mocks")
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks deployed!")


CONTRACT_TO_MOCK = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie
    config if defined, or it will deploy a mock version of that contract
    and return that mock contract.

        Args:
            contract_name (string)

        Returns:
            brownie.network.contract.ProjectContract : The most
            recently deployed version of this contract.
    """
    contract_type = CONTRACT_TO_MOCK[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:  # Eg: MockV3Aggregator.length
            deploy_mocks()
        return contract_type[-1]  # Latest MockV3Aggregator[-1]

    contract_address = config["networks"][network.show_active()][contract_name]
    # Address, # ABI
    contract = Contract.from_abi(
        contract_type._name, contract_address, contract_type.abi
    )
    return contract


def fund_with_link(
    contact_address, account=None, link_token=None, amount=10000000000000000
):  # 0.01 Link
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contact_address, amount, {"from": account})
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contact_address, amount, {"from": account})

    tx.wait(1)
    print("Fund contract!")
    return tx
