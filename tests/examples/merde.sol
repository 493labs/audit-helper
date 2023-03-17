// pragma solidity ^0.8.0;
pragma solidity ^0.5.12;

contract Merde {

    address public owner;
    uint[] public bonusCodes;

    // function pushBonusCode(uint code) public  {
    //     bonusCodes.push(code);
    // }

    function popBonusCode() public  {
        require(bonusCodes.length >= 0);
        bonusCodes.length--; // No pop() method?
        // bonusCodes.pop();
    }

    function modifyBonusCode(uint index, uint update) public {
        // require(index < bonusCodes.length);
        bonusCodes[index] = update;
    }
}