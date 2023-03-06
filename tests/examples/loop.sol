pragma solidity ^0.5.12;
contract Loop {
    function loop(uint x) public  returns (uint y){
        for(int i = 0; i < 3; i++){
            y = y + x;
        }
    }
}
contract NoLoop {
    function add(uint x1, uint x2) internal returns (uint x3){
        x3 = x1 + x2;
        return x3;
    }
    function loop(uint x) public  returns (uint y){
        uint xx = add(x,x);
        y = add(xx,x);
        return y;
    }
}
