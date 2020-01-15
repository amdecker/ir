/**
 * removes duplicate elements from an array
 * @param arr
 */
function removeDuplicates(arr:any[])
{
    let noDup:any[] = [];
    for(let i:number = 0; i < arr.length; i++)
    {
        let shouldAdd:boolean = true;
        for(let n:number = 0; n < noDup.length; n++)
        {
            if(arr[i] == noDup[n])
            {
                shouldAdd = false;
                break;
            }
        }
        if(shouldAdd)
        {
            noDup.push(arr[i]);
        }
    }
    return noDup;
}