pragma solidity ^0.8.0;

contract MyConc{
    function my_func(address payable dst) public payable{
        dst.call{value:msg.value}("");
    }
}