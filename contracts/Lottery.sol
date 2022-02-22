// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is Ownable, VRFConsumerBase {
    address payable[] public players;
    address payable public recentWinner;
    uint256 public randomness;

    uint256 usdEntryFee;
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATES {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATES public currentLotteryState;

    bytes32 public keyHash;
    uint256 public fee;

    uint256 public randomResult;

    event RequestedRandomness(bytes32 requestId);

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        currentLotteryState = LOTTERY_STATES.CLOSED;
        fee = _fee;
        keyHash = _keyHash;
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; // Just to have 18 decimal places too
        // $50, $2000 per 1ETH
        // 50 * 10000 / 2000
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function enter() public payable {
        // $50 min
        require(msg.value >= getEntranceFee(), "Not enough ETH");
        require(
            currentLotteryState == LOTTERY_STATES.OPEN,
            "Lottery not open yet!"
        );
        players.push(payable(msg.sender));
    }

    function startLottery() public onlyOwner {
        require(
            currentLotteryState == LOTTERY_STATES.CLOSED,
            "Cannot start a new lottery yet"
        );
        currentLotteryState = LOTTERY_STATES.OPEN;
    }

    function endLottery() public onlyOwner {
        currentLotteryState = LOTTERY_STATES.CALCULATING_WINNER;
        // This requests a Random Number
        bytes32 requestId = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            currentLotteryState == LOTTERY_STATES.CALCULATING_WINNER,
            "You aren't there yet"
        );
        require(_randomness > 0, "random-not-found");
        // require(lastRequestId == _requestId, "Request IDs don't match");
        uint256 indexOfWinner = _randomness % players.length;

        randomness = _randomness;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        // RESET
        players = new address payable[](0);
        currentLotteryState = LOTTERY_STATES.CLOSED;
    }
}
