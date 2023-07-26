const modifiedVotingSystem =artifacts.require("modifiedVotingSystem");

module.exports=function(deployer){
    deployer.deploy(modifiedVotingSystem);
};
