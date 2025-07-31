# Dhan Data Lake v2

A comprehensive data lake solution for Dhan HQ trading platform that fetches, processes, and stores market data with real-time capabilities.

## 🚀 Features

- **Real-time Market Data**: Live streaming of market data from Dhan HQ API
- **Historical Data Management**: Efficient fetching and storage of historical market data
- **Instrument Master Management**: Comprehensive instrument universe management
- **Data Integrity**: Built-in data validation and integrity checks
- **Scalable Architecture**: Modular design with MongoDB backend
- **Scheduled Operations**: Automated data fetching and processing
- **Rate Limiting**: Intelligent API rate limiting to prevent throttling

## 📁 Project Structure

```
dhan-data-lake-v2/
├── config/                 # Configuration management
├── core/                   # Core functionality (scheduler, universe manager)
├── data_fetchers/          # Data fetching modules
├── database/               # Database operations and collections
├── docs/                   # Documentation
├── logs/                   # Application logs
├── tests/                  # Test suites
├── utils/                  # Utility functions
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd dhan-data-lake-v2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file with your Dhan HQ credentials:
   ```env
   DHAN_CLIENT_ID=your_client_id
   DHAN_ACCESS_TOKEN=your_access_token
   MONGODB_URI=your_mongodb_connection_string
   ```

## 🔧 Configuration

The application uses a modular configuration system. Key configuration files:

- `config/settings.py`: Main application settings
- `config/__init__.py`: Configuration initialization

## 📊 Usage

### Starting the Data Lake
```bash
python main.py
```

### Running Tests
```bash
python -m pytest tests/
```

### Data Integrity Check
```bash
python data_integrity_check.py
```

## 🗄️ Database Collections

The system manages several MongoDB collections:

- **Instrument Master**: Complete instrument universe
- **Historical Data**: Time-series market data
- **Real-time Data**: Live market feeds
- **System Logs**: Application and error logs

## 🔄 Scheduled Operations

The scheduler automatically handles:
- Daily instrument universe updates
- Historical data fetching
- Data integrity checks
- System maintenance tasks

## 📈 API Integration

Integrates with Dhan HQ API for:
- Market data streaming
- Historical data retrieval
- Instrument information
- Real-time quotes

## 🧪 Testing

Comprehensive test suite covering:
- Configuration validation
- Core functionality
- Database operations
- API integrations

## 📝 Logging

Detailed logging system with:
- Application logs
- Error tracking
- Performance monitoring
- Debug information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
- Check the documentation in `docs/`
- Review the API reference
- Contact the development team

## 🔄 Version History

- **v2.0**: Complete rewrite with improved architecture
- **v1.0**: Initial release

---

**Note**: This is a production-ready data lake solution designed for high-frequency trading data management.
