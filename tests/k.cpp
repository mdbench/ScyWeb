#include <iostream>
#include <fstream>
#include <string>
void rot(int n,int* x,int* y,int rx,int ry){ if(ry==0){ if(rx==1){ *x=n-1-*x; *y=n-1-*y; } int t=*x; *x=*y; *y=t; } }
void d2xy(int n,int d,int& x,int& y){ int rx,ry,s,t=d; x=y=0; for(s=1;s<n;s*=2){ rx=1&(t/2); ry=1&(t^rx); rot(s,&x,&y,rx,ry); x+=s*rx; y+=s*ry; t/=4; } }
int main(){
    std::string p="vines_images/cpp_vine.ppm"; std::ofstream o(p,std::ios::binary); o<<"P6\n4000 4000\n255\n"; o.seekp(48000016); o.put(0); o.close();
    std::fstream f(p,std::ios::in|std::ios::out|std::ios::binary); int h=543210;
    for(int i=81;i<=120;i++){
        std::string s="SQL_ID_"+std::to_string(i)+"_DATA"; s+='\0'; int cur=h+(i*1000);
        for(size_t j=0;j<s.length();j+=3){
            int x,y; d2xy(4096,cur,x,y); f.seekg(17+(y*4000+x)*3);
            std::string c=s.substr(j,3); while(c.length()<3) c+='\0';
            f.write(c.c_str(),3); cur++;
        }
    } return 0;
}
