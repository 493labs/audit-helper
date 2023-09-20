pragma solidity ^0.8.0;

contract UnusualAuthenticate1 {
    address owner;
    function setOwner() external{
        owner = msg.sender;
    }
}

contract UnusualAuthenticate2{
    address owner;
    uint supply;
    modifier onlyOwner {
        require(owner == msg.sender);
        _;
    }

    function setSupply(uint _supply) external onlyOwner {
        supply = _supply;
    }

}