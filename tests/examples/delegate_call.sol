pragma solidity ^0.5.12;

contract DelegateCallSimple {
    function delegatecall(address to, bytes memory data ) public {
        to.delegatecall(data);
    }
}

contract DelegateCall {
    address public to;

    function setTo(address _to) public {
        to = _to;
    }

    function delegatecall(bytes memory data ) public {
        to.delegatecall(data);
    }
}
