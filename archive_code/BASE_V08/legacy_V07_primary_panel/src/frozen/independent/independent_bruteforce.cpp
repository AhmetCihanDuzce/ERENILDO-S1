#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
using namespace std;
struct Y {array<int,5> v{};};
int main(int argc,char**argv){
 if(argc!=3){cerr<<"usage: oracle model.txt output.txt\n";return 2;}
 ifstream in(argv[1]); int p,n,cap;in>>p>>n>>cap;
 if(!in||p<2||p>5||n<1||n>24) return 3;
 vector<int> w(n);for(int &z:w)in>>z;
 vector<vector<int>> c(p,vector<int>(n));for(int k=0;k<p;k++)for(int j=0;j<n;j++)in>>c[k][j];
 if(!in)return 4;
 vector<Y> feas;feas.reserve(1<<(n-1));
 uint32_t prev=0;int weight=0;array<int,5> y{};
 for(uint32_t mask=0;mask<(1u<<n);mask++){
  uint32_t gray=mask^(mask>>1);uint32_t delta=gray^prev;
  if(delta){int j=__builtin_ctz(delta);int s=(gray>>j)&1?1:-1;weight+=s*w[j];for(int k=0;k<p;k++)y[k]-=s*c[k][j];}
  prev=gray;
  if(weight<=cap){Y z;z.v=y;feas.push_back(z);}
 }
 sort(feas.begin(),feas.end(),[p](Y const&a,Y const&b){for(int j=0;j<p;j++)if(a.v[j]!=b.v[j])return a.v[j]<b.v[j];return false;});
 vector<Y> front;front.reserve(10000);uint64_t dominated=0;
 for(auto const&cand:feas){
  if(!front.empty()) {bool same=true;for(int j=0;j<p;j++)if(front.back().v[j]!=cand.v[j]){same=false;break;}if(same){dominated++;continue;}}
  bool dom=false;
  for(auto const&f:front){bool all=true;for(int j=1;j<p;j++) if(f.v[j]>cand.v[j]){all=false;break;} if(all){dom=true;break;}}
  if(!dom)front.push_back(cand);else dominated++;
 }
 ofstream out(argv[2]);out<<p<<" "<<n<<" "<<feas.size()<<" "<<front.size()<<"\n";
 for(auto const&z:front){for(int k=0;k<p;k++){if(k)out<<" ";out<<z.v[k];}out<<"\n";}
 cerr<<"ENUM_COMPLETE "<<p<<" "<<n<<" feasible "<<feas.size()<<" Pareto "<<front.size()<<"\n";
 return 0;
}
