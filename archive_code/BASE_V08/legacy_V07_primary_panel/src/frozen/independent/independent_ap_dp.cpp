// Independent exact multiobjective assignment DP for 3 additive minimization objectives.
// For each subset of assigned columns, retains the COMPLETE nondominated cost set
// from assigning first popcount(mask) rows. This is independent of MILP/PEA.
#include <bits/stdc++.h>
using namespace std;
struct Y {int a,b,c; bool operator<(const Y&o) const {return tie(a,b,c)<tie(o.a,o.b,o.c);} bool operator==(const Y&o) const {return tie(a,b,c)==tie(o.a,o.b,o.c);}};
struct BIT {vector<int> b; BIT(int n):b(n+2,INT_MAX){} void put(int i,int z){for(++i;i<(int)b.size();i+=i&-i)b[i]=min(z,b[i]);} int get(int i){int ans=INT_MAX;for(++i;i>0;i-=i&-i) ans=min(ans,b[i]);return ans;}};
int main(int argc,char**argv){
 if(argc<3){cerr<<"usage independent_ap_dp data_integer.txt oracle_points.txt [max_states_per_mask]"<<endl;return 2;}
 ifstream f(argv[1]);int p,n;f>>p>>n;if(p!=3||n>17){cerr<<"Invalid p/n"<<endl;return 2;}
 vector<vector<vector<int>>> cost(3,vector<vector<int>>(n,vector<int>(n)));
 for(int j=0;j<3;j++)for(int i=0;i<n;i++)for(int k=0;k<n;k++)f>>cost[j][i][k];
 if(!f){cerr<<"Invalid costs"<<endl;return 2;}
 int N=1<<n;vector<vector<Y>> dp(N);dp[0].push_back({0,0,0});
 int maxB=n*1000+2;long long totalgenerated=0,totalsurvived=0;
 auto t0=chrono::steady_clock::now();int lastlevel=-1;
 for(int mask=1;mask<N;mask++){
  int lev=__builtin_popcount((unsigned)mask);
  if(lev!=lastlevel){lastlevel=lev; if(lev>1){auto secs=chrono::duration<double>(chrono::steady_clock::now()-t0).count();cerr<<"LEVEL "<<lev<<" elapsed_s "<<secs<<" generated "<<totalgenerated<<" states "<<totalsurvived<<"\n";}}
  vector<Y> cand;int poss=0;
  for(int j=0;j<n;j++)if(mask&(1<<j))poss+=(int)dp[mask^(1<<j)].size();
  cand.reserve(poss);
  for(int j=0;j<n;j++)if(mask&(1<<j)){
   int prev=mask^(1<<j);int row=lev-1;
   for(const auto &v:dp[prev])cand.push_back({v.a+cost[0][row][j],v.b+cost[1][row][j],v.c+cost[2][row][j]});
  }
  totalgenerated+=cand.size();
  sort(cand.begin(),cand.end());
  BIT bit(maxB);
  for(const auto&v:cand){if(bit.get(v.b)<=v.c)continue;dp[mask].push_back(v);bit.put(v.b,v.c);}
  totalsurvived+=dp[mask].size();
  if(mask%2048==0){cerr<<"MASK "<<mask<<"/"<<N<<" current_size "<<dp[mask].size()<<"\n";}
  if(argc>=4&&dp[mask].size()>stoi(argv[3])){cerr<<"SAFETY_LIMIT exceeded "<<mask<<"\n";return 3;}
 }
 ofstream o(argv[2]);for(const auto&v:dp[N-1])o<<v.a<<" "<<v.b<<" "<<v.c<<"\n";
 auto secs=chrono::duration<double>(chrono::steady_clock::now()-t0).count();cerr<<"DONE "<<dp[N-1].size()<<" points in "<<secs<<" sec generated "<<totalgenerated<<" states "<<totalsurvived<<"\n";
}
