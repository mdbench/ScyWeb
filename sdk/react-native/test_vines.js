import React, { useEffect, useState } from 'react';
import { Text, View, ScrollView } from 'react-native';
import ScyKernel from './ScyKernel'; 
import RNFS from 'react-native-fs'; // Common RN Filesystem lib

const TestVines = () => {
  const [log, setLog] = useState("⏳ Initializing React-Native Parity Test...");

  const runTest = async () => {
    const testKey = "User";
    const testValue = "Amanda";
    const password = "ScyWeb_Global_Secret_2026";
    const dbPath = `${RNFS.DocumentDirectoryPath}/rn_vine.ppm`;

    try {
      // RNFS.writeFile handles the 15-byte header parity
      const header = "P6 4000 4000 255\n".substring(0, 15);
      await RNFS.writeFile(dbPath, header, 'ascii');

      // Note: Most RN file libs don't have ftruncate. 
      // We fill the "soil" with null bytes to reach 48,000,015.
      // In a real app, you'd ship a pre-allocated asset.
      const dummyData = "\0".repeat(1024 * 1024); // 1MB chunk
      for(let i = 0; i < 47; i++) {
          await RNFS.appendFile(dbPath, dummyData, 'ascii');
      }

      // INITIALIZE KERNEL
      const scy = new ScyKernel(password, dbPath);

      // SOW: Put operation (Must use 1600 offset internally)
      await scy.put(testKey, testValue);

      // HARVEST: Get operation
      const result = await scy.get(testKey);

      // CLEANUP & VALIDATION
      if (await RNFS.exists(dbPath)) {
        await RNFS.unlink(dbPath);
      }

      if (result === testValue) {
        setLog(prev => prev + `\n✅ RN KV Parity: SUCCESS\n(Recovered: ${result})`);
      } else {
        setLog(prev => prev + `\n❌ RN KV Parity: FAIL\nExpected: ${testValue}, Got: [${result}]`);
      }

    } catch (err) {
      setLog(prev => prev + `\n❌ RN SDK Error: ${err.message}`);
    }
  };

  useEffect(() => { runTest(); }, []);

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#1a1a1a' }}>
      <Text style={{ color: '#00ff00', fontFamily: 'monospace' }}>{log}</Text>
    </ScrollView>
  );
};

export default TestVines;