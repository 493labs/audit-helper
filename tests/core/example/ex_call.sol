// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

interface Token {
    function transfer(address receiver, uint amount) external;
    function get_price() external view returns (uint);
}

contract OutCall1 {
    address token;
    uint price;

    function set_token(address _token) external{
        token = _token;
    }

    function update_price() external {
        price = Token(token).get_price();
    }

    function call_token() external{
        Token(token).transfer(msg.sender, 1);
    }
}

contract OutCall2 {

    function out_call(address tokenAddr, uint amount) external {
        Token t = Token(tokenAddr);
        t.transfer(msg.sender, amount);
        (bool success,bytes memory ret) = address(t).call("");
    }
}