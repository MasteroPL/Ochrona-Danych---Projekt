
function getStats(text){
    var stat = {};
    var c;
    for (var i = 0; i < text.length; i++){
        c = text[i];

        if (c in stat){
            stat[c]++;
        }
        else{
            stat[c] = 1;
        }
    }

    return {
        "stat": stat,
        "num_of_c": text.length
    };
}

function getEntropy(text){
    var entropy = 0.0;
    var stat = getStats(text);
    var p;

    var current;
    for(key in stat["stat"]){
        current = stat["stat"][key];
        p = current / stat["num_of_c"];
        entropy -= (p) * Math.log2(p)
    }
    return entropy
}