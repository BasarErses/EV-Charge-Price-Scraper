# Şarj İstasyonu Fiyat Takip Sistemi - Kurulum Kılavuzu (Windows)

Bu kılavuz, projeyi GitHub'dan indiren bir Windows kullanıcısının sıfırdan kurulum yapması için hazırlanmıştır.

## 1. Hazırlık (Gereksinimler)

Başlamadan önce bilgisayarınızda şunların kurulu olması gerekir:

- **Python (Sürüm 3.10 veya üzeri)**: [Python İndir](https://www.python.org/downloads/) adresinden indirin.
  - *Önemli:* Kurulum sırasında **"Add Python to PATH"** kutucuğunu MUTLAKA işaretleyin.
- **Google Chrome**: Tarayıcının düzgün çalışması için gereklidir.
- **Git (İsteğe bağlı)**: Kodları kolayca indirmek için [Git İndir](https://git-scm.com/download/win) adresinden kurabilirsiniz.

## 2. Adım Adım Kurulum

### Adım 1: Projeyi İndirin

1.  GitHub sayfasına gidin: `https://github.com/BasarErses/EV-Charge-Price-Scraper`
2.  Yeşil **Code** butonuna tıklayın ve **Download ZIP** seçeneğini seçin.
3.  İndirilen ZIP dosyasını masaüstüne veya istediğiniz bir yere **klasöre çıkartın**.

### Adım 2: Komut Satırını Açın

1.  Klasörün içine girin (dosyaların olduğu yer).
2.  Dosya gezgininde üstteki adres çubuğuna tıklayın, oraya `cmd` yazın ve **Enter**'a basın.
    - *Alternatif:* Klasör içinde boş bir yere `Shift + Sağ Tık` yapıp **"PowerShell penceresini buradan aç"** veya **"Komut penceresini buradan aç"** diyebilirsiniz.

### Adım 3: Sanal Ortam Oluşturun

Bu komutu yazıp Enter'a basın:
```bash
python -m venv .venv
```
*(Klasörde `.venv` adında yeni bir klasör oluştuğunu görmelisiniz)*

### Adım 4: Sanal Ortamı Aktif Edin

Şu komutu yazın:
```bash
.venv\Scripts\activate
```
*(Komut satırının en başında `(.venv)` yazısını görmelisiniz. Bu, işlemin başarılı olduğunu gösterir.)*

### Adım 5: Kütüphaneleri Yükleyin

Gerekli tüm paketleri yüklemek için şu komutu çalıştırın:
```bash
pip install -r requirements.txt
```
*(Bu işlem internet hızınıza göre birkaç dakika sürebilir)*

### Adım 6: Tarayıcı Altyapısını Kurun

Site gezintisi için gerekli tarayıcıyı indirin:
```bash
playwright install
```

## 3. Ayarlar

Sistemin çalışması için bir API anahtarına (Claude, Gemini veya Ollama) ihtiyacınız var.

1.  Klasördeki `.env.example` dosyasını bulun.
2.  Adını `.env` olarak değiştirin (sadece `.env` olacak).
3.  Bu dosyayı not defteri ile açın ve API anahtarınızı girin.

    **Örnek (Claude kullanıyorsanız):**
    ```ini
    AI_PROVIDER=claude
    ANTHROPIC_API_KEY=sk-ant-BURAYA-ANAHTARINIZI-YAZIN
    ```

    **Örnek (Gemini kullanıyorsanız):**
    ```ini
    AI_PROVIDER=gemini
    GEMINI_API_KEY=BURAYA-ANAHTARINIZI-YAZIN
    ```

## 4. Çalıştırma

Her şey hazır! Şimdi sistemi başlatın.

1.  Komut satırında (hala `.venv` aktifken) şu komutu yazın:
    ```bash
    python app.py
    ```
2.  Ekranda şöyle bir yazı göreceksiniz:
    `Uvicorn running on http://0.0.0.0:8000`

## 5. Kullanım

1.  İnternet tarayıcınızı açın (Chrome, Edge vb.).
2.  Adres çubuğuna şunu yazın: `http://localhost:8000`
3.  Açılan ekranda **"Start Full Scrape"** butonuna basın.
4.  İşlem bitince (yani %100 olunca) **"Download Prices"** butonu çıkacaktır. Buna basarak Excel (CSV) dosyasını indirebilirsiniz.

## Olası Hatalar

-   **'python' not found**: Python'u kurarken "Add to PATH" seçeneğini unuttunuz veya bilgisayarı yeniden başlatmanız gerekiyor.
-   **Kütüphane hatası**: `.venv\Scripts\activate` komutunu çalıştırmadan `pip install` yapmış olabilirsiniz. Sanal ortamı aktif edip tekrar deneyin.
-   **Yetki hatası (Execution Policy)**: PowerShell'de hata alırsanız `cmd` (Komut İstemi) kullanmayı deneyin.

İyi çalışmalar!
