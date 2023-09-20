pragma solidity ^0.8.0;

contract ContractA {
    uint256 private  _totalSupply;
    uint256 private _allstake;
    mapping (address => uint256) public _balances;
    bool check=true;
    /**
      *  重入锁。
    **/
    modifier nonReentrant(){
        require(check);
        check=false;
        _;
        check=true;
    }
    constructor(){
    }
    /**
      *  根据合约凭证币总量与质押量计算质押价值，10e8为精度处理。
    **/
    function get_price() public view virtual returns (uint256) {
        if(_totalSupply==0||_allstake==0) return 10e8;
        return _totalSupply*10e8/_allstake;
    }
    /**
      *  用户质押，增加质押量并提供凭证币。
    **/
    function deposit() public payable nonReentrant(){
        uint256 mintamount=msg.value*get_price()/10e8;
        _allstake+=msg.value;
        _balances[msg.sender]+=mintamount;
        _totalSupply+=mintamount;
    }
    /**
      *  用户提取，减少质押量并销毁凭证币总量。
    **/
    function withdraw(uint256 burnamount) public nonReentrant(){
        uint256 sendamount=burnamount*10e8/get_price();
        _allstake-=sendamount;
        payable(msg.sender).call{value:sendamount}("");
        _balances[msg.sender]-=burnamount;
        _totalSupply-=burnamount;
    }
}