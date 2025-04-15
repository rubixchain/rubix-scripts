use rubixwasm_std::{errors::WasmError, contract_fn};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AddThreeNumsReq {
    pub a: u32,
    pub b: u32,
    pub c: u32,
}

// A sample smart contract function that adds three numbers.
// Every Rubix Smart Contract function expects a single struct input,
// and the output must be of type Result<String, WasmError>
#[contract_fn]
pub fn add_three_nums(input: AddThreeNumsReq) -> Result<String, WasmError> {
    if input.b == 0 {
        return Err(WasmError::from("Parameter 'b' cannot be zero"))
    }

    let sum = input.a + input.b + input.c;
    Ok(sum.to_string())
}

//eiuwhfiwehfuiwehfiuewhi
//sdkufhsdijfhhefeiufhuies
// dk;jfndsfdfjn
// asldkuhfiufhui 

//ekfhesuifesuifisuf
//sdkfsfshfshfjsd
//dsfjsdfdsfjdskfh
//dlfhsdkjfhsdkfkdfh
//sdkjfhkdjsfkjsdf

//dkfhsdifdsfh
//dskjfhdsiufhsd
//sdkfbhdsfksd

//dslkfhsdhfhsd

//dsf;kjdskjfhsduifdshufsdfsjdfsdf

//sadlhsafdsiuhuidf
//saljfhsadifhdfdas

//dsf;hdfdsdskjhfkjsdhf

//dkfsdhfsdkjfdsjkf

//dljfsdfdshfkjdshfkdjsfksd
//dsjlfsdjkfsdfhsdkjhf

//dskfdjskfhjkdsfhkjsdf

//dskfdskjfhksdjkfhsdf


//dsfkjdsfkjhsdkfdskjf

//sdkfdsjkfksdjfkjdsjfdfjdfj

//dshgfdsfdshfkjsdfh

//isdfsdfhsdfsdfhfdhuhs

//sdlfhskdjfhksdfjkfs