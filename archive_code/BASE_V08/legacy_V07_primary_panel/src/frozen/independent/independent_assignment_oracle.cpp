// Independent exhaustive enumeration of n! permutations, no MILP or PEA.
#include <bits/stdc++.h>
using namespace std;
struct P{int a,b,c; bool operator<(const P&o)const {return tie(a,b,c)<tie(o.a,o.b,o.c);} bool operator==(const P&o)const {return a==o.a&&b==o.b&&c==o.c;}};
int main(int argc,char**argv){if(argc!=3){cerr<<"usage oracle MATRIX_TXT OUTPUT_TXT\n";return 1;}ifstream f(argv[1]);int p,n;f>>p>>n;if(p!=3||n<2||n>11) return 2;vector<vector<vector<int>>> C(3,vector<vector<int>>(n,vector<int>(n)));for(int k=0;k<3;k++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)if(!(f>>C[k][i][j]))return 3;
 vector<int> pi(n);iota(pi.begin(),pi.end(),0);vector<P> V;int64_t ct=0;do{P x{0,0,0};for(int i=0;i<n;i++){x.a+=C[0][i][pi[i]];x.b+=C[1][i][pi[i]];x.c+=C[2][i][pi[i]];}V.push_back(x);ct++;}while(next_permutation(pi.begin(),pi.end()));
 sort(V.begin(),V.end());V.erase(unique(V.begin(),V.end()),V.end());
 vector<int> y;for(auto &x:V)y.push_back(x.b);sort(y.begin(),y.end());y.erase(unique(y.begin(),y.end()),y.end());vector<int>bit(y.size()+1,INT_MAX);auto q=[&](int t){int mi=INT_MAX;for(int i=t;i>0;i-=i&-i)mi=min(mi,bit[i]);return mi;};auto upd=[&](int t,int z){for(int i=t;i<(int)bit.size();i+=i&-i)bit[i]=min(bit[i],z);};
 vector<P>front;for(auto &x:V){int j=lower_bound(y.begin(),y.end(),x.b)-y.begin()+1; if(q(j)<=x.c) continue;front.push_back(x);upd(j,x.c);}ofstream out(argv[2]);out<<ct<<' '<<front.size()<<'\n';for(auto &x:front)out<<x.a<<' '<<x.b<<' '<<x.c<<'\n';cerr<<"enumerated "<<ct<<" distinct cost vectors "<<V.size()<<" efficient "<<front.size()<<"\n";
}
