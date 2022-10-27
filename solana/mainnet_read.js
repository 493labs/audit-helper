import * as sol_web3 from '@solana/web3.js'
import * as spl_token from '@solana/spl-token'
import * as metadata from '@metaplex-foundation/mpl-token-metadata'

import * as fs from "fs"
import path from 'path'
import {fileURLToPath} from 'url'
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const conf = JSON.parse(fs.readFileSync(__dirname+'/config.json'))
const address_str = conf.address
const is_spl_token = conf.is_spl_token
const is_metaplex = conf.is_metaplex

const conn = new sol_web3.Connection('http://solana-mainnet.phantom.tech')

const run = async () => { 
    const address = new sol_web3.PublicKey(address_str)   
    const account_info = await conn.getAccountInfo(address)
    console.log('------------account_info------------')
    console.log(account_info)
    console.log('owner: %s',account_info.owner.toString())

    if (is_spl_token) {
        const token = new spl_token.Token(conn, address, spl_token.TOKEN_PROGRAM_ID, address)
        const mint_info = await token.getMintInfo()
        console.log('------------mint_info------------')
        // 对于nft来说，总供应为1，精度为0，且mint权限为空；但对基于metaplex的token来说，具有mint权限，但实际上无效
        console.log(mint_info)
        console.log('supply: %s', mint_info.supply.toString())

        if (is_metaplex) {
            const pda_key = await metadata.Metadata.getPDA(address)
            const pda = await metadata.Metadata.load(conn,pda_key)
            console.log('------------pda------------')
            console.log(pda)
        }
    }    
}

run()

