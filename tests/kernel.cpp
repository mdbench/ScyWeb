#include <iostream>
#include <fstream>
#include <string>
void rot(int n, int *x, int *y, int rx, int ry) {
    if (ry == 0) { if (rx == 1) { *x = n-1-*x; *y = n-1-*y; } int t = *x; *x = *y; *y = t; }
}
void d2xy(int n, int d, int &x, int &y) {
    int rx, ry, s, t=d; x = y = 0;
    for (s=1; s<n; s*=2) { rx = 1 & (t/2); ry = 1 & (t ^ rx); rot(s, &x, &y, rx, ry); x += s*rx; y += s*ry; t /= 4; }
}
int main() {
    std::string path = "vines_images/cpp_vine.ppm";
    std::ofstream out(path, std::ios::binary); out << "P6\n4000 4000\n255\n"; 
    out.seekp(48000016); out.put(0); out.close();
    std::fstream f(path, std::ios::in | std::ios::out | std::ios::binary);
    int h = 543210; // Shared Seed Logic
    for(int i=81; i<=120; i++){
        std::string sql = "SQL_ID_" + std::to_string(i) + "_CPP_VINE"; sql += '\0';
        int curD = h + (i * 1000);
        for(int j=0; j<sql.length(); j+=3){
            int x, y; d2xy(4096, curD, x, y);
            f.seekg(17 + (y*4000+x)*3); f.write(sql.substr(j,3).c_str(), 3);
            curD++;
        }
    }
    return 0;
}
