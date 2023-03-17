pragma solidity ^0.5.12;

contract Overflow {
    function sub(uint x) public  returns (uint y){
        y = x-10**10;
    }
}
contract NoOverflow {
    function sub(uint x) public  returns (uint y){
        require(x>10**10);
        y = x-10**10;
    }
}
