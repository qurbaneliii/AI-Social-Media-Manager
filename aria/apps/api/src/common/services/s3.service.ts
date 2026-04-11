import { Injectable } from "@nestjs/common";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { randomUUID } from "node:crypto";
import { env } from "../../config/env.js";

@Injectable()
export class S3Service {
  private readonly client = new S3Client({ region: env.awsRegion });

  async presignUpload(fileName: string, mimeType: string): Promise<{ mediaId: string; uploadUrl: string; s3Key: string }> {
    const mediaId = randomUUID();
    const s3Key = `uploads/${mediaId}/${fileName}`;

    const command = new PutObjectCommand({
      Bucket: env.s3Bucket,
      Key: s3Key,
      ContentType: mimeType
    });

    const uploadUrl = await getSignedUrl(this.client, command, { expiresIn: 600 });
    return { mediaId, uploadUrl, s3Key };
  }
}
