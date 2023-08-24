// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

contract reentrant {
    mapping(address => uint256) public userBalances;
    function withdrawBalance() external {  
        uint256 amountToWithdraw = userBalances[msg.sender];
        (bool success, ) = msg.sender.call{value: amountToWithdraw}("");
        require(success);
        userBalances[msg.sender] = 0;
    }
}

contract reentrant2 {
    mapping(address => uint256) public userBalances;

    function withdrawBalance() external {  
        _withdrawBalance();
    }

    function _withdrawBalance() internal {  
        uint256 amountToWithdraw = userBalances[msg.sender];
        (bool success, ) = msg.sender.call{value: amountToWithdraw}("");
        require(success);
        userBalances[msg.sender] = 0;
    }
}