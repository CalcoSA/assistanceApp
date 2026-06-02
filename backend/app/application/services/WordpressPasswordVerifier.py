import hashlib
import base64
import bcrypt
import hmac
import re

class WordpressPasswordVerifier:
    ITOA64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    def verify(self, plainPassword: str, wordpressHash: str) -> bool:
        if not plainPassword or not wordpressHash:
            return False

        if wordpressHash.startswith("$wp$2y$"):
            return self._verifyWordpressBcrypt(plainPassword, wordpressHash)

        if (
            wordpressHash.startswith("$2y$")
            or wordpressHash.startswith("$2a$")
            or wordpressHash.startswith("$2b$")
        ):
            return self._verifyBcrypt(plainPassword, wordpressHash)

        if wordpressHash.startswith("$P$") or wordpressHash.startswith("$H$"):
            return self._verifyPhpass(plainPassword, wordpressHash)

        if re.fullmatch(r"[a-fA-F0-9]{32}", wordpressHash):
            return hmac.compare_digest(
                hashlib.md5(plainPassword.encode("utf-8")).hexdigest(),
                wordpressHash.lower()
            )

        return False

    def _verifyWordpressBcrypt(self, plainPassword: str, wordpressHash: str) -> bool:
        try:
            bcryptHash = wordpressHash[3:]

            if bcryptHash.startswith("$2y$"):
                bcryptHash = "$2b$" + bcryptHash[4:]

            preHashedPassword = base64.b64encode(
                hmac.new(
                    b"wp-sha384",
                    plainPassword.encode("utf-8"),
                    hashlib.sha384
                ).digest()
            )

            return bcrypt.checkpw(
                preHashedPassword,
                bcryptHash.encode("utf-8")
            )

        except Exception:
            return False

    def _verifyBcrypt(self, plainPassword: str, wordpressHash: str) -> bool:
        try:
            bcryptHash = wordpressHash

            if bcryptHash.startswith("$2y$"):
                bcryptHash = "$2b$" + bcryptHash[4:]

            return bcrypt.checkpw(
                plainPassword.encode("utf-8"),
                bcryptHash.encode("utf-8")
            )

        except Exception:
            return False

    def _verifyPhpass(self, plainPassword: str, wordpressHash: str) -> bool:
        try:
            calculatedHash = self._cryptPrivate(plainPassword, wordpressHash)
            return hmac.compare_digest(calculatedHash, wordpressHash)
        except Exception:
            return False

    def _cryptPrivate(self, plainPassword: str, setting: str) -> str:
        output = "*0"

        if setting[:2] == output:
            output = "*1"

        if len(setting) < 12:
            return output

        idValue = setting[:3]

        if idValue not in ("$P$", "$H$"):
            return output

        countLog2 = self.ITOA64.find(setting[3])

        if countLog2 < 7 or countLog2 > 30:
            return output

        count = 1 << countLog2
        salt = setting[4:12]

        if len(salt) != 8:
            return output

        passwordBytes = plainPassword.encode("utf-8")
        hashValue = hashlib.md5(salt.encode("utf-8") + passwordBytes).digest()

        for _ in range(count):
            hashValue = hashlib.md5(hashValue + passwordBytes).digest()

        output = setting[:12]
        output += self._encode64(hashValue, 16)

        return output

    def _encode64(self, inputBytes: bytes, count: int) -> str:
        output = ""
        i = 0

        while i < count:
            value = inputBytes[i]
            i += 1
            output += self.ITOA64[value & 0x3f]

            if i < count:
                value |= inputBytes[i] << 8

            output += self.ITOA64[(value >> 6) & 0x3f]

            if i >= count:
                break

            i += 1

            if i < count:
                value |= inputBytes[i] << 16

            output += self.ITOA64[(value >> 12) & 0x3f]

            if i >= count:
                break

            i += 1
            output += self.ITOA64[(value >> 18) & 0x3f]

        return output