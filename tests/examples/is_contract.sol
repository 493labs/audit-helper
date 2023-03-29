pragma solidity ^0.8.7;

contract Address {
    function is_contract(address account) public view returns (bool){
        return account.code.length > 0;
    }
}