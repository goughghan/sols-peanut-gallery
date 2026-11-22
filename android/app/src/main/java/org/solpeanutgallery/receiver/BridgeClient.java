// SPDX-License-Identifier: GPL-3.0-or-later
package org.solpeanutgallery.receiver;

import android.graphics.BitmapFactory;
import android.graphics.Movie;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Locale;

final class BridgeClient {
    private static final int JSON_LIMIT = 65_536;
    private final String baseUrl;
    private final String token;

    BridgeClient(String baseUrl, String token) throws IOException {
        this.baseUrl = normalizeBaseUrl(baseUrl);
        this.token = token;
    }

    static String normalizeBaseUrl(String value) throws IOException {
        try {
            URI uri = URI.create(value.trim());
            String scheme = uri.getScheme();
            if (!("http".equals(scheme) || "https".equals(scheme)) || uri.getHost() == null
                    || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null) {
                throw new IOException("Bridge URL must be an http(s) origin without credentials, query, or fragment.");
            }
            String normalized = uri.toString();
            while (normalized.endsWith("/")) normalized = normalized.substring(0, normalized.length() - 1);
            return normalized;
        } catch (IllegalArgumentException error) {
            throw new IOException("Bridge URL is invalid.", error);
        }
    }

    static String pair(String baseUrl, String code, String deviceLabel) throws IOException, JSONException {
        String normalized = normalizeBaseUrl(baseUrl);
        JSONObject body = new JSONObject().put("code", code).put("device_label", deviceLabel);
        HttpURLConnection connection = open(normalized + "/v1/pair", "POST", null);
        writeJson(connection, body);
        int status = connection.getResponseCode();
        JSONObject response = readJson(connection, status == 201);
        if (status != 201) throw new IOException(errorMessage(response, status));
        String receiverToken = response.getString("receiver_token");
        if (!receiverToken.matches("pg_rt_[A-Za-z0-9_-]{32,128}")) throw new IOException("Bridge returned an invalid credential.");
        return receiverToken;
    }

    Delivery next() throws IOException, JSONException {
        HttpURLConnection connection = open(baseUrl + "/v1/deliveries/next", "GET", token);
        int status = connection.getResponseCode();
        if (status == 204) {
            connection.disconnect();
            return null;
        }
        JSONObject response = readJson(connection, status == 200);
        if (status != 200) throw new IOException(errorMessage(response, status));
        return Delivery.parse(response);
    }

    File download(Delivery delivery, File cacheDirectory) throws Exception {
        HttpURLConnection connection = open(baseUrl + "/v1/media/" + delivery.mediaId, "GET", token);
        int status = connection.getResponseCode();
        if (status != 200) {
            JSONObject response = readJson(connection, false);
            throw new IOException(errorMessage(response, status));
        }
        String contentType = connection.getHeaderField("Content-Type");
        int contentLength = connection.getContentLength();
        if (!delivery.mimeType.equals(contentType) || contentLength != delivery.byteCount) {
            connection.disconnect();
            throw new IOException("Media response metadata does not match its delivery.");
        }
        byte[] data;
        try (InputStream input = connection.getInputStream()) {
            data = readBounded(input, delivery.byteCount + 1);
        } finally {
            connection.disconnect();
        }
        if (data.length != delivery.byteCount) throw new IOException("Media response length changed in transit.");
        String digest = hex(MessageDigest.getInstance("SHA-256").digest(data));
        if (!MessageDigest.isEqual(digest.getBytes(StandardCharsets.US_ASCII),
                delivery.sha256.getBytes(StandardCharsets.US_ASCII))) {
            throw new IOException("Media SHA-256 does not match its delivery.");
        }
        verifyDecodedMedia(data, delivery);
        File directory = new File(cacheDirectory, "verified-media");
        if (!directory.exists() && !directory.mkdir()) throw new IOException("Cannot create private media cache.");
        File output = new File(directory, delivery.mediaId + ("image/gif".equals(delivery.mimeType) ? ".gif" : ".jpg"));
        try (FileOutputStream stream = new FileOutputStream(output, false)) {
            stream.write(data);
            stream.getFD().sync();
        }
        return output;
    }

    void acknowledge(Delivery delivery, String outcome, String error) throws IOException, JSONException {
        JSONObject body = new JSONObject()
                .put("delivery_id", delivery.deliveryId)
                .put("sequence", delivery.sequence)
                .put("outcome", outcome)
                .put("completed_at", Instant.now().toString());
        if (error != null) body.put("error", error.length() > 180 ? error.substring(0, 180) : error);
        HttpURLConnection connection = open(baseUrl + "/v1/deliveries/" + delivery.deliveryId + "/ack", "POST", token);
        writeJson(connection, body);
        int status = connection.getResponseCode();
        JSONObject response = readJson(connection, status == 200);
        if (status != 200) throw new IOException(errorMessage(response, status));
    }

    private static void verifyDecodedMedia(byte[] data, Delivery delivery) throws IOException {
        int width;
        int height;
        if ("image/jpeg".equals(delivery.mimeType)) {
            if (data.length < 2 || data[0] != (byte) 0xff || data[1] != (byte) 0xd8) throw new IOException("JPEG signature is invalid.");
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeByteArray(data, 0, data.length, options);
            width = options.outWidth;
            height = options.outHeight;
        } else {
            if (data.length < 6 || !(new String(data, 0, 6, StandardCharsets.US_ASCII).equals("GIF87a")
                    || new String(data, 0, 6, StandardCharsets.US_ASCII).equals("GIF89a"))) {
                throw new IOException("GIF signature is invalid.");
            }
            Movie movie = Movie.decodeByteArray(data, 0, data.length);
            if (movie == null) throw new IOException("GIF could not be decoded.");
            width = movie.width();
            height = movie.height();
        }
        if (width != delivery.width || height != delivery.height) throw new IOException("Decoded media dimensions do not match metadata.");
    }

    private static HttpURLConnection open(String address, String method, String bearer) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(10_000);
        connection.setReadTimeout(20_000);
        connection.setRequestMethod(method);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-store");
        if (bearer != null) connection.setRequestProperty("Authorization", "Bearer " + bearer);
        return connection;
    }

    private static void writeJson(HttpURLConnection connection, JSONObject body) throws IOException {
        byte[] data = body.toString().getBytes(StandardCharsets.UTF_8);
        connection.setDoOutput(true);
        connection.setFixedLengthStreamingMode(data.length);
        connection.setRequestProperty("Content-Type", "application/json");
        try (OutputStream output = connection.getOutputStream()) {
            output.write(data);
        }
    }

    private static JSONObject readJson(HttpURLConnection connection, boolean success) throws IOException {
        InputStream input = success ? connection.getInputStream() : connection.getErrorStream();
        try {
            if (input == null) return new JSONObject();
            byte[] data = readBounded(input, JSON_LIMIT);
            return new JSONObject(new String(data, StandardCharsets.UTF_8));
        } catch (JSONException error) {
            throw new IOException("Bridge returned invalid JSON.", error);
        } finally {
            if (input != null) input.close();
            connection.disconnect();
        }
    }

    private static byte[] readBounded(InputStream input, int maximum) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream(Math.min(maximum, 8192));
        byte[] buffer = new byte[8192];
        int total = 0;
        int count;
        while ((count = input.read(buffer)) != -1) {
            total += count;
            if (total > maximum) throw new IOException("Response exceeds its permitted size.");
            output.write(buffer, 0, count);
        }
        return output.toByteArray();
    }

    private static String errorMessage(JSONObject response, int status) {
        return response.optString("message", "Bridge request failed with HTTP " + status + ".");
    }

    private static String hex(byte[] data) {
        StringBuilder value = new StringBuilder(data.length * 2);
        for (byte item : data) value.append(String.format(Locale.ROOT, "%02x", item & 0xff));
        return value.toString();
    }
}
