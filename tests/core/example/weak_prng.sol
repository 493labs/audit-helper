pragma solidity ^0.8.0;

contract Game {

    uint reward_determining_number;

    function guessing() external{
      reward_determining_number = uint256(blockhash(10000)) % 10;
    }
}