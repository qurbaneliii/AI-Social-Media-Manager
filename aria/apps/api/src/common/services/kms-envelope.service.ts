import { Injectable } from "@nestjs/common";
import { randomBytes, createCipheriv, createDecipheriv } from "node:crypto";
import { KMSClient, GenerateDataKeyCommand, DecryptCommand } from "@aws-sdk/client-kms";
import { env } from "../../config/env.js";

@Injectable()
export class KmsEnvelopeService {
  private readonly kms = new KMSClient({ region: env.awsRegion });

  async encrypt(plaintext: string): Promise<{ ciphertext: Buffer; iv: Buffer; tag: Buffer; encryptedDataKey: Buffer }> {
    const dataKey = await this.kms.send(new GenerateDataKeyCommand({
      KeyId: env.kmsKeyId,
      KeySpec: "AES_256"
    }));

    if (!dataKey.Plaintext || !dataKey.CiphertextBlob) {
      throw new Error("Failed to generate data key");
    }

    const iv = randomBytes(12);
    const cipher = createCipheriv("aes-256-gcm", Buffer.from(dataKey.Plaintext), iv);
    const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
    const tag = cipher.getAuthTag();

    return {
      ciphertext,
      iv,
      tag,
      encryptedDataKey: Buffer.from(dataKey.CiphertextBlob)
    };
  }

  async decrypt(ciphertext: Buffer, iv: Buffer, tag: Buffer, encryptedDataKey: Buffer): Promise<string> {
    const keyResponse = await this.kms.send(new DecryptCommand({
      CiphertextBlob: encryptedDataKey
    }));

    if (!keyResponse.Plaintext) {
      throw new Error("Failed to decrypt data key");
    }

    const decipher = createDecipheriv("aes-256-gcm", Buffer.from(keyResponse.Plaintext), iv);
    decipher.setAuthTag(tag);
    const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
    return plaintext.toString("utf8");
  }
}
