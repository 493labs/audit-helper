// pragma solidity ^0.8.0;
pragma solidity ^0.5.12;

contract FeeToken {

    mapping (address => uint) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 value);

    function transfer(address to, uint value) public {
        require(balanceOf[msg.sender] >= value);
        require(balanceOf[to] + value >= balanceOf[to]); // Check for overflows
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        uint256 final_value = value*99/100;
        emit Transfer(msg.sender, to, final_value);
    }
}

contract NoFeeToken {
    
    mapping (address => uint) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 value);

    function transfer(address to, uint value) public {
        require(balanceOf[msg.sender] >= value);
        require(balanceOf[to] + value >= balanceOf[to]); // Check for overflows
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
    }
}