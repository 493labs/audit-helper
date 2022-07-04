import * as sol_web3 from '@solana/web3.js'
import * as spl_token from '@solana/spl-token'
import * as metadata from '@metaplex-foundation/mpl-token-metadata'

const run = async () => {
    const url = 'http://solana-mainnet.phantom.tech'
    
    const conn = new sol_web3.Connection(url)
    const mint = new sol_web3.PublicKey('5PH7seRmF3fAnCHD3BxGJFY9TUsxHkFYAZnQW5a46Fkp')
    const eoa = new sol_web3.PublicKey('TApaymKorUxmHchfsx5f8b8zeVAY9KvqCs3qPva2j9Z')

    const mint_account = await conn.getAccountInfo(mint)
    const eoa_account = await conn.getAccountInfo(eoa)
    console.log('------------mint_account------------')
    console.log(mint_account)
    console.log('------------eoa_account------------')
    console.log(eoa_account)

    const token = new spl_token.Token(conn, mint, spl_token.TOKEN_PROGRAM_ID, mint)
    const mint_info = await token.getMintInfo()
    console.log('------------mint_info------------')
    console.log(mint_info)
    const associated_account = await token.getOrCreateAssociatedAccountInfo(eoa)
    console.log('------------associated_account------------')
    console.log(associated_account)
    // const account_info = await token.getAccountInfo(associated_account.address)  

    const pda_key = await metadata.Metadata.getPDA(mint)
    const pda = await metadata.Metadata.load(conn,pda_key)
    console.log('------------pda------------')
    console.log(pda)
    
}
run()

