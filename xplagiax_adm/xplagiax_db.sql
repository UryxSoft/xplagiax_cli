-- phpMyAdmin SQL Dump
-- version 5.0.4
-- https://www.phpmyadmin.net/
--
-- Servidor: localhost
-- Tiempo de generación: 08-07-2025 a las 19:35:40
-- Versión del servidor: 10.4.17-MariaDB
-- Versión de PHP: 8.0.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `xplagiax_db`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `cleanup_old_logs` (IN `days_to_keep` INT)  BEGIN
    DELETE FROM activity_logs 
    WHERE timestamp < DATE_SUB(CURRENT_TIMESTAMP, INTERVAL days_to_keep DAY);
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `get_session_statistics` (IN `session_id_param` INT)  BEGIN
    SELECT 
        s.id AS session_id,
        s.name AS session_name,
        COUNT(DISTINCT p.id) AS total_participants,
        COUNT(DISTINCT ss.id) AS total_submissions,
        CASE 
            WHEN COUNT(DISTINCT p.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT ss.id) / COUNT(DISTINCT p.id)) * 100 
        END AS submission_rate,
        SUM(IFNULL(ss.file_size, 0)) AS total_file_size,
        s.analysis_completed
    FROM 
        submission_sessions s
    LEFT JOIN 
        session_participants p ON s.id = p.session_id
    LEFT JOIN 
        student_submissions ss ON s.id = ss.session_id
    WHERE 
        s.id = session_id_param
    GROUP BY 
        s.id;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `InsertDocumentAnalysis` (IN `p_analysis_id` VARCHAR(36), IN `p_user_id` INT, IN `p_title` TEXT, IN `p_author` VARCHAR(500), IN `p_pages` INT, IN `p_language` VARCHAR(10), IN `p_metadata_json` JSON, IN `p_summary_json` JSON, IN `p_preview_info_json` JSON, IN `p_images_json` JSON, IN `p_urls_json` JSON, IN `p_annotations_json` JSON)  BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    INSERT INTO document_analyses (
        analysis_id, user_id, title, author, pages, language,
        total_paragraphs, human_count, ai_count, average_confidence,
        preview_success, preview_page_count, full_preview_path, preview_dir,
        annotations, images, urls, preview_page_files
    ) VALUES (
        p_analysis_id, p_user_id, p_title, p_author, p_pages, p_language,
        JSON_EXTRACT(p_summary_json, '$.total_paragraphs'),
        JSON_EXTRACT(p_summary_json, '$.human_count'),
        JSON_EXTRACT(p_summary_json, '$.ai_count'),
        JSON_EXTRACT(p_summary_json, '$.average_confidence'),
        JSON_EXTRACT(p_preview_info_json, '$.success'),
        JSON_EXTRACT(p_preview_info_json, '$.page_count'),
        JSON_UNQUOTE(JSON_EXTRACT(p_preview_info_json, '$.full_preview')),
        JSON_UNQUOTE(JSON_EXTRACT(p_preview_info_json, '$.preview_dir')),
        p_annotations_json, p_images_json, p_urls_json,
        JSON_EXTRACT(p_preview_info_json, '$.page_files')
    );
    
    COMMIT;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` int(11) NOT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Registro de actividades y auditoría';

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `analysis_stats`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `analysis_stats` (
`id` int(11)
,`analysis_id` varchar(36)
,`title` text
,`user_id` int(11)
,`analysis_date` datetime
,`pages` int(11)
,`language` varchar(10)
,`total_paragraphs_counted` bigint(21)
,`human_paragraphs` decimal(22,0)
,`ai_paragraphs` decimal(22,0)
,`avg_confidence` double
,`min_confidence` float
,`max_confidence` float
);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `City`
--

CREATE TABLE `City` (
  `id` int(11) NOT NULL,
  `city` varchar(255) DEFAULT NULL,
  `state_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `City`
--

INSERT INTO `City` (`id`, `city`, `state_id`, `user_id`, `created_date`) VALUES
(1, 'Ancaster', 7, NULL, '2025-06-03 19:03:01'),
(2, 'Antigonish', 5, NULL, '2025-06-03 19:03:01'),
(3, 'Athabasca', 1, NULL, '2025-06-03 19:03:01'),
(4, 'Belleville', 7, NULL, '2025-06-03 19:03:01'),
(5, 'Brandon', 4, NULL, '2025-06-03 19:03:01'),
(6, 'Burnaby', 2, NULL, '2025-06-03 19:03:01'),
(7, 'Calgary', 1, NULL, '2025-06-03 19:03:01'),
(8, 'Charlottetown', 3, NULL, '2025-06-03 19:03:01'),
(9, 'Chicoutimi', 8, NULL, '2025-06-03 19:03:01'),
(10, 'Edmonton', 1, NULL, '2025-06-03 19:03:01'),
(11, 'Etobicoke', 7, NULL, '2025-06-03 19:03:01'),
(12, 'Fredericton', 6, NULL, '2025-06-03 19:03:01'),
(13, 'Gatineau', 8, NULL, '2025-06-03 19:03:01'),
(14, 'Guelph', 7, NULL, '2025-06-03 19:03:01'),
(15, 'Halifax', 5, NULL, '2025-06-03 19:03:01'),
(16, 'Hamilton', 7, NULL, '2025-06-03 19:03:01'),
(17, 'Hearst', 7, NULL, '2025-06-03 19:03:01'),
(18, 'Kamloops', 2, NULL, '2025-06-03 19:03:01'),
(19, 'Kanata', 7, NULL, '2025-06-03 19:03:01'),
(20, 'Kingston', 7, NULL, '2025-06-03 19:03:01'),
(21, 'Kitchener', 7, NULL, '2025-06-03 19:03:01'),
(22, 'Lacombe', 1, NULL, '2025-06-03 19:03:01'),
(23, 'Lakefield', 7, NULL, '2025-06-03 19:03:01'),
(24, 'Langley', 2, NULL, '2025-06-03 19:03:01'),
(25, 'Laval', 8, NULL, '2025-06-03 19:03:01'),
(26, 'Lethbridge', 1, NULL, '2025-06-03 19:03:01'),
(27, 'London', 7, NULL, '2025-06-03 19:03:01'),
(28, 'Mill Bay', 2, NULL, '2025-06-03 19:03:01'),
(29, 'Moncton', 6, NULL, '2025-06-03 19:03:01'),
(30, 'Montreal', 8, NULL, '2025-06-03 19:03:01'),
(31, 'Nanaimo', 2, NULL, '2025-06-03 19:03:01'),
(32, 'New Westminster', 2, NULL, '2025-06-03 19:03:01'),
(33, 'Newmarket', 7, NULL, '2025-06-03 19:03:01'),
(34, 'North Bay', 7, NULL, '2025-06-03 19:03:01'),
(35, 'North Vancouver', 2, NULL, '2025-06-03 19:03:01'),
(36, 'Oakville', 7, NULL, '2025-06-03 19:03:01'),
(37, 'Oshawa', 7, NULL, '2025-06-03 19:03:01'),
(38, 'Ottawa', 7, NULL, '2025-06-03 19:03:01'),
(39, 'Peterborough', 7, NULL, '2025-06-03 19:03:01'),
(40, 'Pointe-de-l Église', 5, NULL, '2025-06-03 19:03:01'),
(41, 'Quebec City', 8, NULL, '2025-06-03 19:03:01'),
(42, 'Richmond Hill', 7, NULL, '2025-06-03 19:03:01'),
(43, 'Rimouski', 8, NULL, '2025-06-03 19:03:01'),
(44, 'Rouyn-Noranda', 8, NULL, '2025-06-03 19:03:01'),
(45, 'Sackville', 6, NULL, '2025-06-03 19:03:01'),
(46, 'Sainte-Anne-de-Bellevue', 8, NULL, '2025-06-03 19:03:01'),
(47, 'Sainte-Thérèse', 8, NULL, '2025-06-03 19:03:01'),
(48, 'Saskatoon', 9, NULL, '2025-06-03 19:03:01'),
(49, 'Sault Ste. Marie', 7, NULL, '2025-06-03 19:03:01'),
(50, 'Sherbrooke', 8, NULL, '2025-06-03 19:03:01'),
(51, 'Squamish', 2, NULL, '2025-06-03 19:03:01'),
(52, 'St. Catharines', 7, NULL, '2025-06-03 19:03:01'),
(53, 'St. Johns', 10, NULL, '2025-06-03 19:03:01'),
(54, 'Sudbury', 7, NULL, '2025-06-03 19:03:01'),
(55, 'Surrey', 2, NULL, '2025-06-03 19:03:01'),
(56, 'Thunder Bay', 7, NULL, '2025-06-03 19:03:01'),
(57, 'Toronto', 7, NULL, '2025-06-03 19:03:01'),
(58, 'Trois-Rivières', 8, NULL, '2025-06-03 19:03:01'),
(59, 'Unionville', 7, NULL, '2025-06-03 19:03:01'),
(60, 'Vancouver', 2, NULL, '2025-06-03 19:03:01'),
(61, 'Victoria', 2, NULL, '2025-06-03 19:03:01'),
(62, 'Waterloo', 7, NULL, '2025-06-03 19:03:01'),
(63, 'Whitehorse', 11, NULL, '2025-06-03 19:03:01'),
(64, 'Windsor', 7, NULL, '2025-06-03 19:03:01'),
(65, 'Winnipeg', 4, NULL, '2025-06-03 19:03:01'),
(66, 'Wolfville', 5, NULL, '2025-06-03 19:03:01');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `classified_paragraphs`
--

CREATE TABLE `classified_paragraphs` (
  `id` int(11) NOT NULL,
  `analysis_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `page_number` int(11) NOT NULL,
  `paragraph_number` int(11) NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_human` tinyint(1) NOT NULL,
  `human_probability` float NOT NULL,
  `ai_probability` float NOT NULL,
  `predicted_model` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `model_scores` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`model_scores`)),
  `final_confidence` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `classified_paragraphs`
--

INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(1, '011383da-f370-425e-a58e-04d8318f6a60', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(2, '011383da-f370-425e-a58e-04d8318f6a60', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(3, '011383da-f370-425e-a58e-04d8318f6a60', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(4, '011383da-f370-425e-a58e-04d8318f6a60', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(5, '011383da-f370-425e-a58e-04d8318f6a60', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(6, '011383da-f370-425e-a58e-04d8318f6a60', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(7, '011383da-f370-425e-a58e-04d8318f6a60', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(8, '011383da-f370-425e-a58e-04d8318f6a60', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(9, '011383da-f370-425e-a58e-04d8318f6a60', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(10, '011383da-f370-425e-a58e-04d8318f6a60', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(11, '011383da-f370-425e-a58e-04d8318f6a60', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(12, '011383da-f370-425e-a58e-04d8318f6a60', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(13, '011383da-f370-425e-a58e-04d8318f6a60', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(14, '011383da-f370-425e-a58e-04d8318f6a60', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(15, '011383da-f370-425e-a58e-04d8318f6a60', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(16, '011383da-f370-425e-a58e-04d8318f6a60', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(17, '011383da-f370-425e-a58e-04d8318f6a60', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(18, '011383da-f370-425e-a58e-04d8318f6a60', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(19, '011383da-f370-425e-a58e-04d8318f6a60', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(20, '011383da-f370-425e-a58e-04d8318f6a60', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(21, '011383da-f370-425e-a58e-04d8318f6a60', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(22, '011383da-f370-425e-a58e-04d8318f6a60', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(23, '011383da-f370-425e-a58e-04d8318f6a60', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(24, '011383da-f370-425e-a58e-04d8318f6a60', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(25, '011383da-f370-425e-a58e-04d8318f6a60', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(26, '011383da-f370-425e-a58e-04d8318f6a60', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(27, '011383da-f370-425e-a58e-04d8318f6a60', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(28, '011383da-f370-425e-a58e-04d8318f6a60', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(29, '011383da-f370-425e-a58e-04d8318f6a60', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(30, '011383da-f370-425e-a58e-04d8318f6a60', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(31, '011383da-f370-425e-a58e-04d8318f6a60', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(32, '011383da-f370-425e-a58e-04d8318f6a60', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(33, '011383da-f370-425e-a58e-04d8318f6a60', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(34, '011383da-f370-425e-a58e-04d8318f6a60', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(35, '011383da-f370-425e-a58e-04d8318f6a60', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(36, '011383da-f370-425e-a58e-04d8318f6a60', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(37, '011383da-f370-425e-a58e-04d8318f6a60', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(38, '011383da-f370-425e-a58e-04d8318f6a60', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(39, '011383da-f370-425e-a58e-04d8318f6a60', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(40, '011383da-f370-425e-a58e-04d8318f6a60', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(41, '011383da-f370-425e-a58e-04d8318f6a60', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(42, '011383da-f370-425e-a58e-04d8318f6a60', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(43, '011383da-f370-425e-a58e-04d8318f6a60', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(44, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(45, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(46, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(47, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(48, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(49, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(50, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(51, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(52, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(53, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(54, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(55, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(56, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(57, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(58, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(59, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(60, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(61, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(62, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(63, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(64, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(65, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(66, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(67, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(68, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(69, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(70, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(71, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(72, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(73, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(74, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(75, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(76, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(77, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(78, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(79, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(80, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(81, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(82, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(83, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(84, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(85, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(86, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(87, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(88, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(89, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(90, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(91, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(92, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(93, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(94, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(95, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(96, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(97, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(98, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(99, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(100, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(101, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(102, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(103, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(104, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(105, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(106, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(107, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(108, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(109, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(110, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(111, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(112, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(113, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(114, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(115, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(116, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(117, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(118, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(119, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(120, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(121, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(122, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(123, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(124, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(125, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(126, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(127, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(128, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(129, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(130, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(131, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(132, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(133, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(134, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(135, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(136, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(137, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(138, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(139, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(140, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(141, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(142, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(143, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(144, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(145, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(146, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(147, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(148, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(149, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(150, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(151, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(152, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(153, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(154, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(155, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(156, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(157, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(158, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(159, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(160, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(161, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(162, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(163, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(164, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(165, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(166, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(167, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(168, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(169, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(170, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(171, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(172, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(173, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(174, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(175, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(176, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(177, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(178, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(179, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(180, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(181, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(182, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(183, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(184, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(185, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(186, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(187, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(188, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(189, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(190, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(191, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(192, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(193, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(194, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(195, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(196, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(197, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(198, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(199, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(200, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(201, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(202, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(203, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(204, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(205, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(206, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(207, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(208, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(209, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(210, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(211, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(212, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(213, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(214, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(215, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(216, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(217, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(218, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(219, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(220, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(221, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(222, '118826f6-d999-44e2-9d21-f97449a35fb7', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(223, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(224, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(225, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(226, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(227, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(228, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(229, '118826f6-d999-44e2-9d21-f97449a35fb7', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(230, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(231, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(232, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(233, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(234, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(235, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(236, '118826f6-d999-44e2-9d21-f97449a35fb7', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(237, '118826f6-d999-44e2-9d21-f97449a35fb7', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(238, '118826f6-d999-44e2-9d21-f97449a35fb7', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(239, '118826f6-d999-44e2-9d21-f97449a35fb7', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(240, '118826f6-d999-44e2-9d21-f97449a35fb7', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(241, '118826f6-d999-44e2-9d21-f97449a35fb7', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(242, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(243, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(244, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(245, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(246, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(247, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(248, '118826f6-d999-44e2-9d21-f97449a35fb7', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(249, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(250, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(251, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(252, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(253, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(254, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(255, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(256, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(257, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(258, '118826f6-d999-44e2-9d21-f97449a35fb7', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(259, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(260, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(261, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(262, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(263, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(264, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(265, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(266, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(267, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(268, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(269, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(270, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(271, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(272, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(273, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(274, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(275, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(276, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(277, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(278, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(279, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(280, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(281, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(282, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(283, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(284, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(285, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(286, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(287, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(288, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(289, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(290, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(291, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(292, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(293, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(294, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(295, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(296, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(297, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(298, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(299, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(300, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(301, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(302, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 2, 'Executive Summary: InsideOut is an innovative AI-based anti-plagiarism platform designed to combat plagiarism in educational institutions', 0, 34.7912, 65.2088, 'text-davinci-002', '{\"GLM130B\": 17.189572751522064, \"mixtral-8x7b\": 2.6393288746476173, \"t0_11b\": 4.0702201426029205, \"text-davinci-002\": 17.61145442724228, \"text-davinci-003\": 10.206353664398193}', 65.2088),
(303, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 3, 'Our main objective is to maximize creativity and foster a sense of academic inquiry among students, thus promoting an honest and ethical learning environment', 0, 26.7912, 73.2088, 'gpt-3.5-turbo', '{\"gpt-3.5-turbo\": 35.59751510620117, \"t0_11b\": 6.153709068894386, \"t0_3b\": 3.5969678312540054, \"text-davinci-002\": 8.487856388092041, \"text-davinci-003\": 5.080416798591614}', 73.2088);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(304, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 4, 'The platform provides a number of unique features including cross-institutional plagiarism analysis of text and image content, detection of text generated by ChatGPT and other generative artificial intelligence, misspelling correction, web content search, and content similarity analysis', 0, 4.1347, 95.8653, 't0_11b', '{\"flan_t5_base\": 1.6046172007918358, \"flan_t5_large\": 2.8542449697852135, \"t0_11b\": 49.39051866531372, \"t0_3b\": 38.61706256866455}', 95.8653),
(305, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 7, 'Description of the Problem: Plagiarism is a growing problem in the educational field that affects both students and institutions', 0, 32.5515, 67.4485, 't0_11b', '{\"flan_t5_base\": 4.279111325740814, \"mixtral-8x7b\": 10.04665121436119, \"t0_11b\": 24.730731546878815, \"t0_3b\": 5.417586490511894, \"text-davinci-002\": 7.389088720083237}', 67.4485),
(306, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 8, 'The ease of access to information online has led to an increase in the unauthorized copying of academic work, which undermines the integrity of the educational process and impairs the development of students\' research and creative skills', 0, 0.266481, 99.7335, 't0_11b', '{\"flan_t5_large\": 3.681693598628044, \"opt_iml_max_1.3b\": 2.316890098154545, \"t0_11b\": 49.343547224998474, \"t0_3b\": 28.487905859947205, \"text-davinci-002\": 6.573188304901123}', 99.7335),
(307, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 9, 'Educational institutions need an effective and reliable solution to detect and prevent plagiarism in all its forms', 1, 63.9201, 36.0799, NULL, '{\"GLM130B\": 8.88151153922081, \"mixtral-8x7b\": 1.282153557986021, \"text-davinci-002\": 19.972364604473114, \"text-davinci-003\": 2.1296149119734764}', 63.9201),
(308, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 11, 'Solution: InsideOut offers a comprehensive and advanced solution to combat plagiarism in the educational field', 0, 17.1419, 82.8581, 'text-davinci-003', '{\"GLM130B\": 13.40470165014267, \"gpt-3.5-turbo\": 5.179885029792786, \"mixtral-8x7b\": 5.457092821598053, \"text-davinci-002\": 16.333551704883575, \"text-davinci-003\": 32.56323039531708}', 82.8581),
(309, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 12, 'Our platform uses cutting-edge artificial intelligence technologies to analyze and compare the content of academic papers, identifying similarities with other sources and detecting possible cases of plagiarism', 1, 59.5056, 40.4944, NULL, '{\"GLM130B\": 3.435087949037552, \"t0_11b\": 22.006650269031525, \"t0_3b\": 5.61041496694088, \"text-davinci-002\": 2.6990821585059166}', 59.5056),
(310, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 13, 'Some key features of our platform are: Closed Platform: Exclusive access for teachers, guaranteeing the confidentiality and security of student work', 1, 84.5385, 15.4615, NULL, '{\"GLM130B\": 2.055578865110874, \"t0_11b\": 2.185641787946224, \"text-davinci-002\": 4.045836254954338}', 84.5385),
(311, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 14, 'Plagiarism Analysis in Text and Image Content: Our technology is capable of detecting similarities in text and also in images, which provides greater precision in detecting unauthorized copies', 0, 17.4969, 82.5031, 't0_11b', '{\"flan_t5_base\": 6.495032459497452, \"flan_t5_large\": 6.5967366099357605, \"flan_t5_small\": 4.8472534865140915, \"t0_11b\": 32.95668363571167, \"t0_3b\": 12.875215709209442}', 82.5031),
(312, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 15, 'Detection of Text Generated by ChatGPT and Generative Artificial Intelligences: Our system is capable of identifying content generated by artificial intelligences, ensuring that students do not use text generation tools to plagiarize', 0, 5.43632, 94.5637, 't0_11b', '{\"flan_t5_base\": 19.314628839492798, \"flan_t5_large\": 11.790917068719864, \"flan_t5_small\": 18.37548017501831, \"t0_11b\": 21.08389586210251, \"t0_3b\": 18.47861558198929}', 94.5637),
(313, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 16, 'Misspelling Detection: In addition to detecting similarities, InsideOut also checks spelling to ensure that papers are original and well-written', 1, 73.6687, 26.3313, NULL, '{\"gpt-3.5-turbo\": 2.6648202911019325, \"t0_11b\": 5.883374810218811, \"t0_3b\": 2.075725793838501, \"text-davinci-002\": 1.7024783417582512, \"text-davinci-003\": 5.8012377470731735}', 73.6687),
(314, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 17, 'Search for Content on the Web: The platform performs an exhaustive search on the Internet to detect possible sources of plagiarism and provide detailed reports on the matches found', 1, 62.4909, 37.5091, NULL, '{\"flan_t5_base\": 2.192106656730175, \"flan_t5_large\": 2.660263143479824, \"t0_11b\": 11.364849656820297, \"t0_3b\": 7.287091016769409, \"text-davinci-002\": 2.0945167168974876}', 62.4909),
(315, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 18, 'Patent Similarity Analysis: For research projects with technical or scientific content, InsideOut includes comparison with patent databases, thus avoiding plagiarism of protected ideas', 1, 97.8795, 2.12049, NULL, '{}', 97.8795),
(316, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 20, 'Customer Experience: Our focus is on providing the best possible experience for our customers', 1, 50.0103, 49.9897, NULL, '{\"GLM130B\": 1.697506569325924, \"mixtral-8x7b\": 1.1426224373281002, \"t0_11b\": 1.7292225733399391, \"text-davinci-002\": 28.86699140071869, \"text-davinci-003\": 10.905804485082626}', 50.0103),
(317, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 21, 'By choosing InsideOut, users get: Intuitive and Easy-to-Use Platform: We designed the InsideOut interface to be accessible and friendly for all users, facilitating its use for both teachers and students', 0, 2.78419, 97.2158, 't0_11b', '{\"flan_t5_base\": 2.111664228141308, \"flan_t5_large\": 2.7485137805342674, \"flan_t5_small\": 2.590731717646122, \"t0_11b\": 44.29624080657959, \"t0_3b\": 33.054742217063904}', 97.2158),
(318, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 22, 'Security and Credibility of Stored Data: Data privacy and security are fundamental to us', 1, 67.9209, 32.0791, NULL, '{\"GLM130B\": 3.81806343793869, \"flan_t5_base\": 1.6611652448773384, \"t0_11b\": 5.668074265122414, \"t0_3b\": 2.6519715785980225, \"text-davinci-002\": 7.87830650806427}', 67.9209),
(319, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 23, 'We implement advanced security measures to ensure the protection of our clients\' confidential information', 0, 23.6684, 76.3316, 'gemma-7b-it', '{\"gemma-7b-it\": 26.38586461544037, \"mixtral-8x7b\": 5.387815460562706, \"t0_11b\": 3.7576675415039062, \"text-davinci-002\": 8.640476316213608, \"text-davinci-003\": 22.325773537158966}', 76.3316),
(320, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 24, 'Specialized Technical Support: Our highly trained technical support team is available to provide fast and efficient assistance in case of any technical questions or problems', 1, 67.8985, 32.1015, NULL, '{\"GLM130B\": 1.7315765842795372, \"flan_t5_large\": 1.5009776689112186, \"t0_11b\": 1.5083316713571548, \"text-davinci-002\": 3.854537010192871, \"text-davinci-003\": 6.691845506429672}', 67.8985),
(321, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 25, 'Regular Data Backup: We make regular backups of the data stored on the platform, ensuring the integrity and availability of the information at all times', 0, 35.0788, 64.9212, 'text-davinci-003', '{\"gpt-3.5-turbo\": 3.2395143061876297, \"mixtral-8x7b\": 3.2010111957788467, \"t0_11b\": 11.624302715063095, \"text-davinci-002\": 3.401462361216545, \"text-davinci-003\": 21.197418868541718}', 64.9212),
(322, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 26, 'Personalization and Flexibility: We understand that each educational institution is unique, which is why we offer the ability to customize the platform according to the needs and policies of each client', 0, 14.0477, 85.9523, 't0_11b', '{\"flan_t5_small\": 4.9144405871629715, \"t0_11b\": 28.912988305091858, \"t0_3b\": 18.495512008666992, \"text-davinci-002\": 7.851459830999374, \"text-davinci-003\": 6.970493495464325}', 85.9523),
(323, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 27, 'We also provide integration options with existing learning management systems for a seamless transition', 1, 93.3003, 6.69972, NULL, '{\"text-davinci-002\": 1.0723466984927654}', 93.3003),
(324, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 28, 'Advanced Report Analysis: Our platform offers detailed reports on detected plagiarism, allowing teachers and administrators to gain deep insight into student academic performance and integrity', 0, 36.8714, 63.1286, 'text-davinci-003', '{\"GLM130B\": 3.960046172142029, \"t0_11b\": 8.131694793701172, \"t0_3b\": 5.973988398909569, \"text-davinci-002\": 5.981653928756714, \"text-davinci-003\": 9.79878082871437}', 63.1286),
(325, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 29, 'Continuous Updates: We are committed to constantly improving InsideOut through updates and improvements based on feedback from our users and technological advances', 0, 42.5372, 57.4628, 't0_11b', '{\"flan_t5_base\": 2.3616431280970573, \"opt_13b\": 5.59544712305069, \"opt_iml_30b\": 2.5573261082172394, \"t0_11b\": 19.75000947713852, \"t0_3b\": 7.285204529762268}', 57.4628),
(326, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 31, 'Business Model: InsideOut will operate under a subscription model for educational institutions', 1, 91.9563, 8.04375, NULL, '{\"GLM130B\": 3.001341037452221, \"mixtral-8x7b\": 1.0399391874670982, \"text-davinci-002\": 1.5248077921569347}', 91.9563),
(327, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 1, 32, 'We will offer different plans depending on the size of the institution and the frequency of use of the platform', 1, 91.2909, 8.70912, NULL, '{\"flan_t5_small\": 1.155210193246603, \"t0_11b\": 2.4119162932038307, \"t0_3b\": 1.2752223759889603}', 91.2909),
(328, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 1, 'will offer customized versions for those institutions that wish to integrate InsideOut with their existing learning management systems', 1, 95.6812, 4.31884, NULL, '{\"text-davinci-002\": 1.7887072637677193}', 95.6812),
(329, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 2, 'We will also explore the possibility of offering individual plans for students who wish to verify their work before submitting it', 1, 50.8838, 49.1162, NULL, '{\"bloomz\": 5.97538985311985, \"mixtral-8x7b\": 2.6466546580195427, \"t0_11b\": 8.890213817358017, \"t0_3b\": 7.22789466381073, \"text-davinci-002\": 8.18437859416008}', 50.8838),
(330, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 4, 'Future Vision: Our vision is to make InsideOut the world\'s leading solution to combat plagiarism in educational institutions', 0, 38.3778, 61.6222, 'text-davinci-002', '{\"GLM130B\": 8.547049760818481, \"t0_11b\": 7.936743646860123, \"t0_3b\": 2.687281370162964, \"text-davinci-002\": 23.24804663658142, \"text-davinci-003\": 2.6593580842018127}', 61.6222),
(331, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 5, 'We aspire to be recognized as the gold standard in academic integrity, thereby helping to foster genuine inquiry and creativity in future generations of students', 0, 20.0697, 79.9303, 'gpt-3.5-turbo', '{\"gemma-7b-it\": 8.667504787445068, \"gpt-3.5-turbo\": 18.802092969417572, \"llama3-70b\": 6.971973925828934, \"llama3-8b\": 7.694951444864273, \"t0_11b\": 13.913755118846893}', 79.9303),
(332, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 6, 'In the future, we plan to expand our presence internationally and collaborate with educational and government organizations to promote academic integrity on a global scale', 0, 13.6667, 86.3333, 't0_11b', '{\"flan_t5_base\": 4.916928336024284, \"flan_t5_large\": 4.35618944466114, \"flan_t5_small\": 3.1140193343162537, \"t0_11b\": 43.71527135372162, \"t0_3b\": 25.554487109184265}', 86.3333),
(333, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 8, 'Future Innovations: In our commitment to continue to be a leader in the field of academic integrity, we are planning to implement the following innovations in the future: Multimodal Analysis: We will improve our platform so that it can analyze not only text and images, but also content in more complex formats, such as videos and presentations, thus extending plagiarism detection to new forms of academic presentation', 1, 62.2276, 37.7724, NULL, '{\"opt_2.7b\": 2.3746097460389137, \"opt_30b\": 2.2592948749661446, \"opt_6.7b\": 3.5849109292030334, \"opt_iml_30b\": 13.941952586174011, \"opt_iml_max_1.3b\": 9.568029642105103}', 62.2276),
(334, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 9, 'Paraphrase Identification: We will develop advanced techniques to detect paraphrases and rewriting of texts, which will allow us to identify more sophisticated and subtle cases of plagiarism', 0, 5.38276, 94.6172, 't0_11b', '{\"flan_t5_base\": 7.789625972509384, \"flan_t5_large\": 6.5559931099414825, \"flan_t5_small\": 6.732261925935745, \"t0_11b\": 39.389920234680176, \"t0_3b\": 24.289600551128387}', 94.6172),
(335, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 10, 'Integration with Conversational Artificial Intelligence: We will take advantage of the capabilities of conversational artificial intelligence to improve the user experience, allowing teachers to interact with the platform and obtain results faster', 0, 2.44282, 97.5572, 't0_11b', '{\"flan_t5_base\": 4.838467016816139, \"flan_t5_large\": 3.8294803351163864, \"flan_t5_small\": 5.2231717854738235, \"t0_11b\": 44.13602352142334, \"t0_3b\": 28.322163224220276}', 97.5572),
(336, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 11, 'Media Content Analysis: We will implement media analysis recognition technologies to detect plagiarism in recorded speech and live broadcast content, thus addressing new forms of unauthorized copying', 0, 16.1308, 83.8692, 't0_11b', '{\"flan_t5_base\": 9.361135959625244, \"flan_t5_large\": 8.757440000772476, \"flan_t5_small\": 7.2495609521865845, \"t0_11b\": 24.598436057567596, \"t0_3b\": 17.43338257074356}', 83.8692),
(337, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 12, 'Generative Adversarial Neural Networks (GANs): We will investigate the use of GANs to help students prevent plagiarism from the stage of creating academic papers', 0, 6.83418, 93.1658, 't0_11b', '{\"flan_t5_base\": 10.402149707078934, \"flan_t5_large\": 4.183986410498619, \"flan_t5_small\": 3.9208736270666122, \"t0_11b\": 37.08020746707916, \"t0_3b\": 28.949549794197083}', 93.1658),
(338, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 14, 'Conclusions: InsideOut is positioned as the most advanced and reliable anti-plagiarism platform on the market', 1, 79.5706, 20.4294, NULL, '{\"GLM130B\": 5.401511117815971, \"t0_11b\": 1.0953069664537907, \"text-davinci-002\": 5.5885422974824905, \"text-davinci-003\": 3.899930790066719}', 79.5706),
(339, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 15, 'Our focus on plagiarism detection in various types of content and backed by an exceptional customer experience set us apart from other solutions available', 1, 91.6106, 8.38936, NULL, '{\"GLM130B\": 1.2019029818475246, \"opt_13b\": 1.9402652978897095}', 91.6106),
(340, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 16, 'With InsideOut, educational institutions can guarantee the originality and authenticity of their students\' work, promoting an ethical and nurturing learning environment', 0, 35.3269, 64.6731, 'text-davinci-003', '{\"gemma-7b-it\": 8.96531343460083, \"gpt-3.5-turbo\": 16.732025146484375, \"llama3-8b\": 5.431848764419556, \"text-davinci-002\": 4.360374808311462, \"text-davinci-003\": 17.930257320404053}', 64.6731),
(341, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', 2, 17, 'We look to the future with enthusiasm, committed to continuing to develop innovative technologies that protect academic integrity and foster creativity in the world of education', 0, 4.54033, 95.4597, 't0_11b', '{\"flan_t5_base\": 3.2098721712827682, \"flan_t5_large\": 5.282832682132721, \"t0_11b\": 45.47313749790192, \"t0_3b\": 19.274163246154785, \"text-davinci-002\": 4.117799177765846}', 95.4597),
(342, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 1, 7, '5      environment:        - ETCD_AUTO_COMPACTION_MODE=revision        - ETCD_AUTO_COMPACTION_RETENTION=1000        - ETCD_QUOTA_BACKEND_BYTES=4294967296        - ETCD_SNAPSHOT_COUNT=50000      volumes:        - ${DOCKER_VOLUME_DIRECTORY:-', 0, 42.7184, 57.2816, 'text-davinci-003', '{\"davinci\": 8.572840690612793, \"gpt-3.5-turbo\": 9.359171241521835, \"gpt-35\": 2.838836796581745, \"text-davinci-002\": 3.152669593691826, \"text-davinci-003\": 15.798325836658478}', 57.2816),
(343, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 1, 14, '0:2379 --data-dir /etcd      healthcheck:        test: [\"CMD\", \"etcdctl\", \"endpoint\", \"health\"]        interval: 30s        timeout: 20s        retries: 3     minio:      container_name: milvus-minio      image: minio/minio:RELEASE', 0, 49.2197, 50.7803, 'bloomz', '{\"bloomz\": 8.488673716783524, \"t0_11b\": 7.612870633602142, \"t0_3b\": 3.8640473037958145, \"text-davinci-002\": 6.772323697805405, \"text-davinci-003\": 2.9539451003074646}', 50.7803),
(344, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 1, 15, '2023-03-20T20-16-18Z      environment:        MINIO_ACCESS_KEY: minioadmin        MINIO_SECRET_KEY: minioadmin      ports:        - \"9001:9001\"        - \"9000:9000\"      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 1, 50.758, 49.242, NULL, '{\"flan_t5_base\": 5.061525478959084, \"gpt-3.5-turbo\": 2.86224577575922, \"mixtral-8x7b\": 4.059778526425362, \"t0_3b\": 4.1207145899534225, \"text-davinci-003\": 8.93961787223816}', 50.758),
(345, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 1, 16, '}/volumes/minio:/minio_data      command: minio server /minio_data --console-address  \":9001\"      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9000/minio/health/live\"]        interval: 30s        timeout: 20s        retries: 3     standalone:      container_name: milvus-standalone', 0, 25.7935, 74.2065, 'bloomz', '{\"bloomz\": 50.73360800743103, \"gpt-3.5-turbo\": 2.1616751328110695, \"llama3-70b\": 2.0342105999588966, \"llama3-8b\": 1.7069177702069283, \"mixtral-8x7b\": 6.467520445585251}', 74.2065),
(346, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 2, 5, '5      command: [\"milvus\", \"run\", \"standalone\"]      security_opt:      - seccomp:unconfined      environment:        ETCD_ENDPOINTS: etcd:2379        MINIO_ADDRESS: minio:9000      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 0, 19.3757, 80.6243, 'text-davinci-003', '{\"flan_t5_base\": 7.812297344207764, \"gpt_neox\": 4.666187986731529, \"t0_3b\": 4.060305655002594, \"text-davinci-002\": 10.072479397058487, \"text-davinci-003\": 15.303091704845428}', 80.6243),
(347, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', 2, 6, '}/volumes/milvus:/var/lib/milvus      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9091/healthz\"]        interval: 30s        start_period: 90s        timeout: 20s        retries: 3      ports:        - \"19530:19530\"        - \"9091:9091\"      depends_on:        - \"etcd\"        - \"minio\"   networks:    default:      name: milvus', 0, 31.7145, 68.2855, 'bloomz', '{\"bloomz\": 53.6054790019989, \"dolly\": 3.0257053673267365, \"gemma-7b-it\": 1.8954822793602943, \"gpt-3.5-turbo\": 2.3315174505114555, \"mixtral-8x7b\": 2.1952033042907715}', 68.2855),
(348, 'bb5b45da-4192-4597-801c-07ef26415758', 1, 7, '5      environment:        - ETCD_AUTO_COMPACTION_MODE=revision        - ETCD_AUTO_COMPACTION_RETENTION=1000        - ETCD_QUOTA_BACKEND_BYTES=4294967296        - ETCD_SNAPSHOT_COUNT=50000      volumes:        - ${DOCKER_VOLUME_DIRECTORY:-', 0, 42.7184, 57.2816, 'text-davinci-003', '{\"davinci\": 8.572840690612793, \"gpt-3.5-turbo\": 9.359171241521835, \"gpt-35\": 2.838836796581745, \"text-davinci-002\": 3.152669593691826, \"text-davinci-003\": 15.798325836658478}', 57.2816),
(349, 'bb5b45da-4192-4597-801c-07ef26415758', 1, 14, '0:2379 --data-dir /etcd      healthcheck:        test: [\"CMD\", \"etcdctl\", \"endpoint\", \"health\"]        interval: 30s        timeout: 20s        retries: 3     minio:      container_name: milvus-minio      image: minio/minio:RELEASE', 0, 49.2197, 50.7803, 'bloomz', '{\"bloomz\": 8.488673716783524, \"t0_11b\": 7.612870633602142, \"t0_3b\": 3.8640473037958145, \"text-davinci-002\": 6.772323697805405, \"text-davinci-003\": 2.9539451003074646}', 50.7803),
(350, 'bb5b45da-4192-4597-801c-07ef26415758', 1, 15, '2023-03-20T20-16-18Z      environment:        MINIO_ACCESS_KEY: minioadmin        MINIO_SECRET_KEY: minioadmin      ports:        - \"9001:9001\"        - \"9000:9000\"      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 1, 50.758, 49.242, NULL, '{\"flan_t5_base\": 5.061525478959084, \"gpt-3.5-turbo\": 2.86224577575922, \"mixtral-8x7b\": 4.059778526425362, \"t0_3b\": 4.1207145899534225, \"text-davinci-003\": 8.93961787223816}', 50.758),
(351, 'bb5b45da-4192-4597-801c-07ef26415758', 1, 16, '}/volumes/minio:/minio_data      command: minio server /minio_data --console-address  \":9001\"      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9000/minio/health/live\"]        interval: 30s        timeout: 20s        retries: 3     standalone:      container_name: milvus-standalone', 0, 25.7935, 74.2065, 'bloomz', '{\"bloomz\": 50.73360800743103, \"gpt-3.5-turbo\": 2.1616751328110695, \"llama3-70b\": 2.0342105999588966, \"llama3-8b\": 1.7069177702069283, \"mixtral-8x7b\": 6.467520445585251}', 74.2065),
(352, 'bb5b45da-4192-4597-801c-07ef26415758', 2, 5, '5      command: [\"milvus\", \"run\", \"standalone\"]      security_opt:      - seccomp:unconfined      environment:        ETCD_ENDPOINTS: etcd:2379        MINIO_ADDRESS: minio:9000      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 0, 19.3757, 80.6243, 'text-davinci-003', '{\"flan_t5_base\": 7.812297344207764, \"gpt_neox\": 4.666187986731529, \"t0_3b\": 4.060305655002594, \"text-davinci-002\": 10.072479397058487, \"text-davinci-003\": 15.303091704845428}', 80.6243),
(353, 'bb5b45da-4192-4597-801c-07ef26415758', 2, 6, '}/volumes/milvus:/var/lib/milvus      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9091/healthz\"]        interval: 30s        start_period: 90s        timeout: 20s        retries: 3      ports:        - \"19530:19530\"        - \"9091:9091\"      depends_on:        - \"etcd\"        - \"minio\"   networks:    default:      name: milvus', 0, 31.7145, 68.2855, 'bloomz', '{\"bloomz\": 53.6054790019989, \"dolly\": 3.0257053673267365, \"gemma-7b-it\": 1.8954822793602943, \"gpt-3.5-turbo\": 2.3315174505114555, \"mixtral-8x7b\": 2.1952033042907715}', 68.2855),
(354, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(355, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(356, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(357, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(358, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(359, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(360, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(361, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(362, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(363, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(364, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(365, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(366, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(367, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(368, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(369, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(370, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(371, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(372, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(373, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(374, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(375, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(376, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(377, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(378, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(379, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(380, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(381, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(382, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(383, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(384, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(385, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(386, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(387, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(388, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(389, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(390, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(391, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(392, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(393, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(394, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(395, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(396, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(397, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 1, 7, '5      environment:        - ETCD_AUTO_COMPACTION_MODE=revision        - ETCD_AUTO_COMPACTION_RETENTION=1000        - ETCD_QUOTA_BACKEND_BYTES=4294967296        - ETCD_SNAPSHOT_COUNT=50000      volumes:        - ${DOCKER_VOLUME_DIRECTORY:-', 0, 42.7184, 57.2816, 'text-davinci-003', '{\"davinci\": 8.572840690612793, \"gpt-3.5-turbo\": 9.359171241521835, \"gpt-35\": 2.838836796581745, \"text-davinci-002\": 3.152669593691826, \"text-davinci-003\": 15.798325836658478}', 57.2816),
(398, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 1, 14, '0:2379 --data-dir /etcd      healthcheck:        test: [\"CMD\", \"etcdctl\", \"endpoint\", \"health\"]        interval: 30s        timeout: 20s        retries: 3     minio:      container_name: milvus-minio      image: minio/minio:RELEASE', 0, 49.2197, 50.7803, 'bloomz', '{\"bloomz\": 8.488673716783524, \"t0_11b\": 7.612870633602142, \"t0_3b\": 3.8640473037958145, \"text-davinci-002\": 6.772323697805405, \"text-davinci-003\": 2.9539451003074646}', 50.7803),
(399, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 1, 15, '2023-03-20T20-16-18Z      environment:        MINIO_ACCESS_KEY: minioadmin        MINIO_SECRET_KEY: minioadmin      ports:        - \"9001:9001\"        - \"9000:9000\"      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 1, 50.758, 49.242, NULL, '{\"flan_t5_base\": 5.061525478959084, \"gpt-3.5-turbo\": 2.86224577575922, \"mixtral-8x7b\": 4.059778526425362, \"t0_3b\": 4.1207145899534225, \"text-davinci-003\": 8.93961787223816}', 50.758),
(400, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 1, 16, '}/volumes/minio:/minio_data      command: minio server /minio_data --console-address  \":9001\"      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9000/minio/health/live\"]        interval: 30s        timeout: 20s        retries: 3     standalone:      container_name: milvus-standalone', 0, 25.7935, 74.2065, 'bloomz', '{\"bloomz\": 50.73360800743103, \"gpt-3.5-turbo\": 2.1616751328110695, \"llama3-70b\": 2.0342105999588966, \"llama3-8b\": 1.7069177702069283, \"mixtral-8x7b\": 6.467520445585251}', 74.2065),
(401, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 2, 5, '5      command: [\"milvus\", \"run\", \"standalone\"]      security_opt:      - seccomp:unconfined      environment:        ETCD_ENDPOINTS: etcd:2379        MINIO_ADDRESS: minio:9000      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 0, 19.3757, 80.6243, 'text-davinci-003', '{\"flan_t5_base\": 7.812297344207764, \"gpt_neox\": 4.666187986731529, \"t0_3b\": 4.060305655002594, \"text-davinci-002\": 10.072479397058487, \"text-davinci-003\": 15.303091704845428}', 80.6243),
(402, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', 2, 6, '}/volumes/milvus:/var/lib/milvus      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9091/healthz\"]        interval: 30s        start_period: 90s        timeout: 20s        retries: 3      ports:        - \"19530:19530\"        - \"9091:9091\"      depends_on:        - \"etcd\"        - \"minio\"   networks:    default:      name: milvus', 0, 31.7145, 68.2855, 'bloomz', '{\"bloomz\": 53.6054790019989, \"dolly\": 3.0257053673267365, \"gemma-7b-it\": 1.8954822793602943, \"gpt-3.5-turbo\": 2.3315174505114555, \"mixtral-8x7b\": 2.1952033042907715}', 68.2855),
(403, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(404, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(405, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(406, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(407, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(408, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(409, '0f47b067-e033-4de1-9f1d-cd3021480e88', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(410, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(411, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(412, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(413, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(414, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(415, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(416, '0f47b067-e033-4de1-9f1d-cd3021480e88', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(417, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(418, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(419, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(420, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(421, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(422, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(423, '0f47b067-e033-4de1-9f1d-cd3021480e88', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(424, '0f47b067-e033-4de1-9f1d-cd3021480e88', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(425, '0f47b067-e033-4de1-9f1d-cd3021480e88', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(426, '0f47b067-e033-4de1-9f1d-cd3021480e88', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(427, '0f47b067-e033-4de1-9f1d-cd3021480e88', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(428, '0f47b067-e033-4de1-9f1d-cd3021480e88', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(429, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(430, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(431, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(432, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(433, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(434, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(435, '0f47b067-e033-4de1-9f1d-cd3021480e88', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(436, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(437, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(438, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(439, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(440, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(441, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(442, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(443, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(444, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(445, '0f47b067-e033-4de1-9f1d-cd3021480e88', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(446, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(447, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(448, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(449, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(450, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(451, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(452, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(453, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(454, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(455, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(456, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(457, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(458, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(459, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(460, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(461, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(462, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(463, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(464, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(465, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(466, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(467, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(468, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(469, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(470, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(471, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(472, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(473, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(474, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(475, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(476, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(477, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(478, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(479, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(480, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(481, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(482, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(483, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(484, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(485, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(486, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(487, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(488, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(489, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(490, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(491, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(492, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(493, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(494, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(495, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(496, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(497, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(498, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(499, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(500, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(501, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(502, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(503, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(504, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(505, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(506, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(507, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(508, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(509, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(510, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(511, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(512, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(513, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(514, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(515, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(516, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(517, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(518, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(519, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(520, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(521, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(522, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(523, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(524, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(525, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(526, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(527, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(528, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(529, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(530, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(531, '08c2ae2d-90f7-4584-9b5e-20c897586e58', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(532, '8cad1d41-98be-461e-9864-645902b6955c', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(533, '8cad1d41-98be-461e-9864-645902b6955c', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(534, '8cad1d41-98be-461e-9864-645902b6955c', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(535, '8cad1d41-98be-461e-9864-645902b6955c', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(536, '8cad1d41-98be-461e-9864-645902b6955c', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(537, '8cad1d41-98be-461e-9864-645902b6955c', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(538, '8cad1d41-98be-461e-9864-645902b6955c', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(539, '8cad1d41-98be-461e-9864-645902b6955c', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(540, '8cad1d41-98be-461e-9864-645902b6955c', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(541, '8cad1d41-98be-461e-9864-645902b6955c', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(542, '8cad1d41-98be-461e-9864-645902b6955c', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(543, '8cad1d41-98be-461e-9864-645902b6955c', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(544, '8cad1d41-98be-461e-9864-645902b6955c', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(545, '8cad1d41-98be-461e-9864-645902b6955c', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(546, '8cad1d41-98be-461e-9864-645902b6955c', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(547, '8cad1d41-98be-461e-9864-645902b6955c', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(548, '8cad1d41-98be-461e-9864-645902b6955c', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(549, '8cad1d41-98be-461e-9864-645902b6955c', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(550, '8cad1d41-98be-461e-9864-645902b6955c', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(551, '8cad1d41-98be-461e-9864-645902b6955c', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(552, '8cad1d41-98be-461e-9864-645902b6955c', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(553, '8cad1d41-98be-461e-9864-645902b6955c', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(554, '8cad1d41-98be-461e-9864-645902b6955c', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(555, '8cad1d41-98be-461e-9864-645902b6955c', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(556, '8cad1d41-98be-461e-9864-645902b6955c', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(557, '8cad1d41-98be-461e-9864-645902b6955c', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(558, '8cad1d41-98be-461e-9864-645902b6955c', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(559, '8cad1d41-98be-461e-9864-645902b6955c', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(560, '8cad1d41-98be-461e-9864-645902b6955c', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(561, '8cad1d41-98be-461e-9864-645902b6955c', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(562, '8cad1d41-98be-461e-9864-645902b6955c', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(563, '8cad1d41-98be-461e-9864-645902b6955c', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(564, '8cad1d41-98be-461e-9864-645902b6955c', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(565, '8cad1d41-98be-461e-9864-645902b6955c', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(566, '8cad1d41-98be-461e-9864-645902b6955c', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(567, '8cad1d41-98be-461e-9864-645902b6955c', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(568, '8cad1d41-98be-461e-9864-645902b6955c', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(569, '8cad1d41-98be-461e-9864-645902b6955c', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(570, '8cad1d41-98be-461e-9864-645902b6955c', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(571, '8cad1d41-98be-461e-9864-645902b6955c', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(572, '8cad1d41-98be-461e-9864-645902b6955c', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(573, '8cad1d41-98be-461e-9864-645902b6955c', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(574, '8cad1d41-98be-461e-9864-645902b6955c', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(575, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(576, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(577, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(578, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(579, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(580, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(581, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(582, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(583, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(584, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(585, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(586, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(587, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(588, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(589, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(590, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(591, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(592, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(593, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(594, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(595, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(596, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(597, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(598, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(599, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(600, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(601, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(602, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(603, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(604, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(605, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(606, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(607, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(608, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(609, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(610, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(611, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(612, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(613, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(614, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(615, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(616, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(617, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(618, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 2, 'Executive Summary: InsideOut is an innovative AI-based anti-plagiarism platform designed to combat plagiarism in educational institutions', 0, 34.7912, 65.2088, 'text-davinci-002', '{\"GLM130B\": 17.189572751522064, \"mixtral-8x7b\": 2.6393288746476173, \"t0_11b\": 4.0702201426029205, \"text-davinci-002\": 17.61145442724228, \"text-davinci-003\": 10.206353664398193}', 65.2088),
(619, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 3, 'Our main objective is to maximize creativity and foster a sense of academic inquiry among students, thus promoting an honest and ethical learning environment', 0, 26.7912, 73.2088, 'gpt-3.5-turbo', '{\"gpt-3.5-turbo\": 35.59751510620117, \"t0_11b\": 6.153709068894386, \"t0_3b\": 3.5969678312540054, \"text-davinci-002\": 8.487856388092041, \"text-davinci-003\": 5.080416798591614}', 73.2088),
(620, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 4, 'The platform provides a number of unique features including cross-institutional plagiarism analysis of text and image content, detection of text generated by ChatGPT and other generative artificial intelligence, misspelling correction, web content search, and content similarity analysis', 0, 4.1347, 95.8653, 't0_11b', '{\"flan_t5_base\": 1.6046172007918358, \"flan_t5_large\": 2.8542449697852135, \"t0_11b\": 49.39051866531372, \"t0_3b\": 38.61706256866455}', 95.8653),
(621, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 7, 'Description of the Problem: Plagiarism is a growing problem in the educational field that affects both students and institutions', 0, 32.5515, 67.4485, 't0_11b', '{\"flan_t5_base\": 4.279111325740814, \"mixtral-8x7b\": 10.04665121436119, \"t0_11b\": 24.730731546878815, \"t0_3b\": 5.417586490511894, \"text-davinci-002\": 7.389088720083237}', 67.4485),
(622, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 8, 'The ease of access to information online has led to an increase in the unauthorized copying of academic work, which undermines the integrity of the educational process and impairs the development of students\' research and creative skills', 0, 0.266481, 99.7335, 't0_11b', '{\"flan_t5_large\": 3.681693598628044, \"opt_iml_max_1.3b\": 2.316890098154545, \"t0_11b\": 49.343547224998474, \"t0_3b\": 28.487905859947205, \"text-davinci-002\": 6.573188304901123}', 99.7335),
(623, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 9, 'Educational institutions need an effective and reliable solution to detect and prevent plagiarism in all its forms', 1, 63.9201, 36.0799, NULL, '{\"GLM130B\": 8.88151153922081, \"mixtral-8x7b\": 1.282153557986021, \"text-davinci-002\": 19.972364604473114, \"text-davinci-003\": 2.1296149119734764}', 63.9201),
(624, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 11, 'Solution: InsideOut offers a comprehensive and advanced solution to combat plagiarism in the educational field', 0, 17.1419, 82.8581, 'text-davinci-003', '{\"GLM130B\": 13.40470165014267, \"gpt-3.5-turbo\": 5.179885029792786, \"mixtral-8x7b\": 5.457092821598053, \"text-davinci-002\": 16.333551704883575, \"text-davinci-003\": 32.56323039531708}', 82.8581),
(625, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 12, 'Our platform uses cutting-edge artificial intelligence technologies to analyze and compare the content of academic papers, identifying similarities with other sources and detecting possible cases of plagiarism', 1, 59.5056, 40.4944, NULL, '{\"GLM130B\": 3.435087949037552, \"t0_11b\": 22.006650269031525, \"t0_3b\": 5.61041496694088, \"text-davinci-002\": 2.6990821585059166}', 59.5056),
(626, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 13, 'Some key features of our platform are: Closed Platform: Exclusive access for teachers, guaranteeing the confidentiality and security of student work', 1, 84.5385, 15.4615, NULL, '{\"GLM130B\": 2.055578865110874, \"t0_11b\": 2.185641787946224, \"text-davinci-002\": 4.045836254954338}', 84.5385),
(627, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 14, 'Plagiarism Analysis in Text and Image Content: Our technology is capable of detecting similarities in text and also in images, which provides greater precision in detecting unauthorized copies', 0, 17.4969, 82.5031, 't0_11b', '{\"flan_t5_base\": 6.495032459497452, \"flan_t5_large\": 6.5967366099357605, \"flan_t5_small\": 4.8472534865140915, \"t0_11b\": 32.95668363571167, \"t0_3b\": 12.875215709209442}', 82.5031),
(628, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 15, 'Detection of Text Generated by ChatGPT and Generative Artificial Intelligences: Our system is capable of identifying content generated by artificial intelligences, ensuring that students do not use text generation tools to plagiarize', 0, 5.43632, 94.5637, 't0_11b', '{\"flan_t5_base\": 19.314628839492798, \"flan_t5_large\": 11.790917068719864, \"flan_t5_small\": 18.37548017501831, \"t0_11b\": 21.08389586210251, \"t0_3b\": 18.47861558198929}', 94.5637),
(629, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 16, 'Misspelling Detection: In addition to detecting similarities, InsideOut also checks spelling to ensure that papers are original and well-written', 1, 73.6687, 26.3313, NULL, '{\"gpt-3.5-turbo\": 2.6648202911019325, \"t0_11b\": 5.883374810218811, \"t0_3b\": 2.075725793838501, \"text-davinci-002\": 1.7024783417582512, \"text-davinci-003\": 5.8012377470731735}', 73.6687),
(630, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 17, 'Search for Content on the Web: The platform performs an exhaustive search on the Internet to detect possible sources of plagiarism and provide detailed reports on the matches found', 1, 62.4909, 37.5091, NULL, '{\"flan_t5_base\": 2.192106656730175, \"flan_t5_large\": 2.660263143479824, \"t0_11b\": 11.364849656820297, \"t0_3b\": 7.287091016769409, \"text-davinci-002\": 2.0945167168974876}', 62.4909),
(631, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 18, 'Patent Similarity Analysis: For research projects with technical or scientific content, InsideOut includes comparison with patent databases, thus avoiding plagiarism of protected ideas', 1, 97.8795, 2.12049, NULL, '{}', 97.8795),
(632, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 20, 'Customer Experience: Our focus is on providing the best possible experience for our customers', 1, 50.0103, 49.9897, NULL, '{\"GLM130B\": 1.697506569325924, \"mixtral-8x7b\": 1.1426224373281002, \"t0_11b\": 1.7292225733399391, \"text-davinci-002\": 28.86699140071869, \"text-davinci-003\": 10.905804485082626}', 50.0103),
(633, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 21, 'By choosing InsideOut, users get: Intuitive and Easy-to-Use Platform: We designed the InsideOut interface to be accessible and friendly for all users, facilitating its use for both teachers and students', 0, 2.78419, 97.2158, 't0_11b', '{\"flan_t5_base\": 2.111664228141308, \"flan_t5_large\": 2.7485137805342674, \"flan_t5_small\": 2.590731717646122, \"t0_11b\": 44.29624080657959, \"t0_3b\": 33.054742217063904}', 97.2158),
(634, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 22, 'Security and Credibility of Stored Data: Data privacy and security are fundamental to us', 1, 67.9209, 32.0791, NULL, '{\"GLM130B\": 3.81806343793869, \"flan_t5_base\": 1.6611652448773384, \"t0_11b\": 5.668074265122414, \"t0_3b\": 2.6519715785980225, \"text-davinci-002\": 7.87830650806427}', 67.9209),
(635, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 23, 'We implement advanced security measures to ensure the protection of our clients\' confidential information', 0, 23.6684, 76.3316, 'gemma-7b-it', '{\"gemma-7b-it\": 26.38586461544037, \"mixtral-8x7b\": 5.387815460562706, \"t0_11b\": 3.7576675415039062, \"text-davinci-002\": 8.640476316213608, \"text-davinci-003\": 22.325773537158966}', 76.3316),
(636, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 24, 'Specialized Technical Support: Our highly trained technical support team is available to provide fast and efficient assistance in case of any technical questions or problems', 1, 67.8985, 32.1015, NULL, '{\"GLM130B\": 1.7315765842795372, \"flan_t5_large\": 1.5009776689112186, \"t0_11b\": 1.5083316713571548, \"text-davinci-002\": 3.854537010192871, \"text-davinci-003\": 6.691845506429672}', 67.8985),
(637, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 25, 'Regular Data Backup: We make regular backups of the data stored on the platform, ensuring the integrity and availability of the information at all times', 0, 35.0788, 64.9212, 'text-davinci-003', '{\"gpt-3.5-turbo\": 3.2395143061876297, \"mixtral-8x7b\": 3.2010111957788467, \"t0_11b\": 11.624302715063095, \"text-davinci-002\": 3.401462361216545, \"text-davinci-003\": 21.197418868541718}', 64.9212),
(638, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 26, 'Personalization and Flexibility: We understand that each educational institution is unique, which is why we offer the ability to customize the platform according to the needs and policies of each client', 0, 14.0477, 85.9523, 't0_11b', '{\"flan_t5_small\": 4.9144405871629715, \"t0_11b\": 28.912988305091858, \"t0_3b\": 18.495512008666992, \"text-davinci-002\": 7.851459830999374, \"text-davinci-003\": 6.970493495464325}', 85.9523),
(639, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 27, 'We also provide integration options with existing learning management systems for a seamless transition', 1, 93.3003, 6.69972, NULL, '{\"text-davinci-002\": 1.0723466984927654}', 93.3003),
(640, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 28, 'Advanced Report Analysis: Our platform offers detailed reports on detected plagiarism, allowing teachers and administrators to gain deep insight into student academic performance and integrity', 0, 36.8714, 63.1286, 'text-davinci-003', '{\"GLM130B\": 3.960046172142029, \"t0_11b\": 8.131694793701172, \"t0_3b\": 5.973988398909569, \"text-davinci-002\": 5.981653928756714, \"text-davinci-003\": 9.79878082871437}', 63.1286),
(641, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 29, 'Continuous Updates: We are committed to constantly improving InsideOut through updates and improvements based on feedback from our users and technological advances', 0, 42.5372, 57.4628, 't0_11b', '{\"flan_t5_base\": 2.3616431280970573, \"opt_13b\": 5.59544712305069, \"opt_iml_30b\": 2.5573261082172394, \"t0_11b\": 19.75000947713852, \"t0_3b\": 7.285204529762268}', 57.4628),
(642, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 31, 'Business Model: InsideOut will operate under a subscription model for educational institutions', 1, 91.9563, 8.04375, NULL, '{\"GLM130B\": 3.001341037452221, \"mixtral-8x7b\": 1.0399391874670982, \"text-davinci-002\": 1.5248077921569347}', 91.9563),
(643, '7936f838-793e-4d44-ab72-82cebce6e216', 1, 32, 'We will offer different plans depending on the size of the institution and the frequency of use of the platform', 1, 91.2909, 8.70912, NULL, '{\"flan_t5_small\": 1.155210193246603, \"t0_11b\": 2.4119162932038307, \"t0_3b\": 1.2752223759889603}', 91.2909),
(644, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 1, 'will offer customized versions for those institutions that wish to integrate InsideOut with their existing learning management systems', 1, 95.6812, 4.31884, NULL, '{\"text-davinci-002\": 1.7887072637677193}', 95.6812),
(645, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 2, 'We will also explore the possibility of offering individual plans for students who wish to verify their work before submitting it', 1, 50.8838, 49.1162, NULL, '{\"bloomz\": 5.97538985311985, \"mixtral-8x7b\": 2.6466546580195427, \"t0_11b\": 8.890213817358017, \"t0_3b\": 7.22789466381073, \"text-davinci-002\": 8.18437859416008}', 50.8838),
(646, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 4, 'Future Vision: Our vision is to make InsideOut the world\'s leading solution to combat plagiarism in educational institutions', 0, 38.3778, 61.6222, 'text-davinci-002', '{\"GLM130B\": 8.547049760818481, \"t0_11b\": 7.936743646860123, \"t0_3b\": 2.687281370162964, \"text-davinci-002\": 23.24804663658142, \"text-davinci-003\": 2.6593580842018127}', 61.6222),
(647, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 5, 'We aspire to be recognized as the gold standard in academic integrity, thereby helping to foster genuine inquiry and creativity in future generations of students', 0, 20.0697, 79.9303, 'gpt-3.5-turbo', '{\"gemma-7b-it\": 8.667504787445068, \"gpt-3.5-turbo\": 18.802092969417572, \"llama3-70b\": 6.971973925828934, \"llama3-8b\": 7.694951444864273, \"t0_11b\": 13.913755118846893}', 79.9303),
(648, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 6, 'In the future, we plan to expand our presence internationally and collaborate with educational and government organizations to promote academic integrity on a global scale', 0, 13.6667, 86.3333, 't0_11b', '{\"flan_t5_base\": 4.916928336024284, \"flan_t5_large\": 4.35618944466114, \"flan_t5_small\": 3.1140193343162537, \"t0_11b\": 43.71527135372162, \"t0_3b\": 25.554487109184265}', 86.3333),
(649, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 8, 'Future Innovations: In our commitment to continue to be a leader in the field of academic integrity, we are planning to implement the following innovations in the future: Multimodal Analysis: We will improve our platform so that it can analyze not only text and images, but also content in more complex formats, such as videos and presentations, thus extending plagiarism detection to new forms of academic presentation', 1, 62.2276, 37.7724, NULL, '{\"opt_2.7b\": 2.3746097460389137, \"opt_30b\": 2.2592948749661446, \"opt_6.7b\": 3.5849109292030334, \"opt_iml_30b\": 13.941952586174011, \"opt_iml_max_1.3b\": 9.568029642105103}', 62.2276),
(650, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 9, 'Paraphrase Identification: We will develop advanced techniques to detect paraphrases and rewriting of texts, which will allow us to identify more sophisticated and subtle cases of plagiarism', 0, 5.38276, 94.6172, 't0_11b', '{\"flan_t5_base\": 7.789625972509384, \"flan_t5_large\": 6.5559931099414825, \"flan_t5_small\": 6.732261925935745, \"t0_11b\": 39.389920234680176, \"t0_3b\": 24.289600551128387}', 94.6172),
(651, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 10, 'Integration with Conversational Artificial Intelligence: We will take advantage of the capabilities of conversational artificial intelligence to improve the user experience, allowing teachers to interact with the platform and obtain results faster', 0, 2.44282, 97.5572, 't0_11b', '{\"flan_t5_base\": 4.838467016816139, \"flan_t5_large\": 3.8294803351163864, \"flan_t5_small\": 5.2231717854738235, \"t0_11b\": 44.13602352142334, \"t0_3b\": 28.322163224220276}', 97.5572),
(652, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 11, 'Media Content Analysis: We will implement media analysis recognition technologies to detect plagiarism in recorded speech and live broadcast content, thus addressing new forms of unauthorized copying', 0, 16.1308, 83.8692, 't0_11b', '{\"flan_t5_base\": 9.361135959625244, \"flan_t5_large\": 8.757440000772476, \"flan_t5_small\": 7.2495609521865845, \"t0_11b\": 24.598436057567596, \"t0_3b\": 17.43338257074356}', 83.8692),
(653, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 12, 'Generative Adversarial Neural Networks (GANs): We will investigate the use of GANs to help students prevent plagiarism from the stage of creating academic papers', 0, 6.83418, 93.1658, 't0_11b', '{\"flan_t5_base\": 10.402149707078934, \"flan_t5_large\": 4.183986410498619, \"flan_t5_small\": 3.9208736270666122, \"t0_11b\": 37.08020746707916, \"t0_3b\": 28.949549794197083}', 93.1658),
(654, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 14, 'Conclusions: InsideOut is positioned as the most advanced and reliable anti-plagiarism platform on the market', 1, 79.5706, 20.4294, NULL, '{\"GLM130B\": 5.401511117815971, \"t0_11b\": 1.0953069664537907, \"text-davinci-002\": 5.5885422974824905, \"text-davinci-003\": 3.899930790066719}', 79.5706),
(655, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 15, 'Our focus on plagiarism detection in various types of content and backed by an exceptional customer experience set us apart from other solutions available', 1, 91.6106, 8.38936, NULL, '{\"GLM130B\": 1.2019029818475246, \"opt_13b\": 1.9402652978897095}', 91.6106),
(656, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 16, 'With InsideOut, educational institutions can guarantee the originality and authenticity of their students\' work, promoting an ethical and nurturing learning environment', 0, 35.3269, 64.6731, 'text-davinci-003', '{\"gemma-7b-it\": 8.96531343460083, \"gpt-3.5-turbo\": 16.732025146484375, \"llama3-8b\": 5.431848764419556, \"text-davinci-002\": 4.360374808311462, \"text-davinci-003\": 17.930257320404053}', 64.6731),
(657, '7936f838-793e-4d44-ab72-82cebce6e216', 2, 17, 'We look to the future with enthusiasm, committed to continuing to develop innovative technologies that protect academic integrity and foster creativity in the world of education', 0, 4.54033, 95.4597, 't0_11b', '{\"flan_t5_base\": 3.2098721712827682, \"flan_t5_large\": 5.282832682132721, \"t0_11b\": 45.47313749790192, \"t0_3b\": 19.274163246154785, \"text-davinci-002\": 4.117799177765846}', 95.4597),
(658, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 1, 7, '5      environment:        - ETCD_AUTO_COMPACTION_MODE=revision        - ETCD_AUTO_COMPACTION_RETENTION=1000        - ETCD_QUOTA_BACKEND_BYTES=4294967296        - ETCD_SNAPSHOT_COUNT=50000      volumes:        - ${DOCKER_VOLUME_DIRECTORY:-', 0, 42.7184, 57.2816, 'text-davinci-003', '{\"davinci\": 8.572840690612793, \"gpt-3.5-turbo\": 9.359171241521835, \"gpt-35\": 2.838836796581745, \"text-davinci-002\": 3.152669593691826, \"text-davinci-003\": 15.798325836658478}', 57.2816),
(659, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 1, 14, '0:2379 --data-dir /etcd      healthcheck:        test: [\"CMD\", \"etcdctl\", \"endpoint\", \"health\"]        interval: 30s        timeout: 20s        retries: 3     minio:      container_name: milvus-minio      image: minio/minio:RELEASE', 0, 49.2197, 50.7803, 'bloomz', '{\"bloomz\": 8.488673716783524, \"t0_11b\": 7.612870633602142, \"t0_3b\": 3.8640473037958145, \"text-davinci-002\": 6.772323697805405, \"text-davinci-003\": 2.9539451003074646}', 50.7803),
(660, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 1, 15, '2023-03-20T20-16-18Z      environment:        MINIO_ACCESS_KEY: minioadmin        MINIO_SECRET_KEY: minioadmin      ports:        - \"9001:9001\"        - \"9000:9000\"      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 1, 50.758, 49.242, NULL, '{\"flan_t5_base\": 5.061525478959084, \"gpt-3.5-turbo\": 2.86224577575922, \"mixtral-8x7b\": 4.059778526425362, \"t0_3b\": 4.1207145899534225, \"text-davinci-003\": 8.93961787223816}', 50.758),
(661, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 1, 16, '}/volumes/minio:/minio_data      command: minio server /minio_data --console-address  \":9001\"      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9000/minio/health/live\"]        interval: 30s        timeout: 20s        retries: 3     standalone:      container_name: milvus-standalone', 0, 25.7935, 74.2065, 'bloomz', '{\"bloomz\": 50.73360800743103, \"gpt-3.5-turbo\": 2.1616751328110695, \"llama3-70b\": 2.0342105999588966, \"llama3-8b\": 1.7069177702069283, \"mixtral-8x7b\": 6.467520445585251}', 74.2065),
(662, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 2, 5, '5      command: [\"milvus\", \"run\", \"standalone\"]      security_opt:      - seccomp:unconfined      environment:        ETCD_ENDPOINTS: etcd:2379        MINIO_ADDRESS: minio:9000      volumes:        -  ${DOCKER_VOLUME_DIRECTORY:-', 0, 19.3757, 80.6243, 'text-davinci-003', '{\"flan_t5_base\": 7.812297344207764, \"gpt_neox\": 4.666187986731529, \"t0_3b\": 4.060305655002594, \"text-davinci-002\": 10.072479397058487, \"text-davinci-003\": 15.303091704845428}', 80.6243),
(663, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', 2, 6, '}/volumes/milvus:/var/lib/milvus      healthcheck:        test: [\"CMD\", \"curl\", \"-f\",  \"http://localhost:9091/healthz\"]        interval: 30s        start_period: 90s        timeout: 20s        retries: 3      ports:        - \"19530:19530\"        - \"9091:9091\"      depends_on:        - \"etcd\"        - \"minio\"   networks:    default:      name: milvus', 0, 31.7145, 68.2855, 'bloomz', '{\"bloomz\": 53.6054790019989, \"dolly\": 3.0257053673267365, \"gemma-7b-it\": 1.8954822793602943, \"gpt-3.5-turbo\": 2.3315174505114555, \"mixtral-8x7b\": 2.1952033042907715}', 68.2855),
(664, '452ef92a-edae-4328-83f1-200c8071b925', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(665, '452ef92a-edae-4328-83f1-200c8071b925', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(666, '452ef92a-edae-4328-83f1-200c8071b925', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(667, '452ef92a-edae-4328-83f1-200c8071b925', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(668, '452ef92a-edae-4328-83f1-200c8071b925', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(669, '452ef92a-edae-4328-83f1-200c8071b925', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(670, '452ef92a-edae-4328-83f1-200c8071b925', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(671, '452ef92a-edae-4328-83f1-200c8071b925', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(672, '452ef92a-edae-4328-83f1-200c8071b925', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(673, '452ef92a-edae-4328-83f1-200c8071b925', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(674, '452ef92a-edae-4328-83f1-200c8071b925', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(675, '452ef92a-edae-4328-83f1-200c8071b925', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(676, '452ef92a-edae-4328-83f1-200c8071b925', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(677, '452ef92a-edae-4328-83f1-200c8071b925', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(678, '452ef92a-edae-4328-83f1-200c8071b925', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(679, '452ef92a-edae-4328-83f1-200c8071b925', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(680, '452ef92a-edae-4328-83f1-200c8071b925', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(681, '452ef92a-edae-4328-83f1-200c8071b925', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(682, '452ef92a-edae-4328-83f1-200c8071b925', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(683, '452ef92a-edae-4328-83f1-200c8071b925', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(684, '452ef92a-edae-4328-83f1-200c8071b925', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(685, '452ef92a-edae-4328-83f1-200c8071b925', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(686, '452ef92a-edae-4328-83f1-200c8071b925', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(687, '452ef92a-edae-4328-83f1-200c8071b925', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(688, '452ef92a-edae-4328-83f1-200c8071b925', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(689, '452ef92a-edae-4328-83f1-200c8071b925', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(690, '452ef92a-edae-4328-83f1-200c8071b925', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(691, '452ef92a-edae-4328-83f1-200c8071b925', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(692, '452ef92a-edae-4328-83f1-200c8071b925', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(693, '452ef92a-edae-4328-83f1-200c8071b925', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(694, '452ef92a-edae-4328-83f1-200c8071b925', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(695, '452ef92a-edae-4328-83f1-200c8071b925', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(696, '452ef92a-edae-4328-83f1-200c8071b925', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(697, '452ef92a-edae-4328-83f1-200c8071b925', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(698, '452ef92a-edae-4328-83f1-200c8071b925', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(699, '452ef92a-edae-4328-83f1-200c8071b925', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(700, '452ef92a-edae-4328-83f1-200c8071b925', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(701, '452ef92a-edae-4328-83f1-200c8071b925', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(702, '452ef92a-edae-4328-83f1-200c8071b925', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(703, '452ef92a-edae-4328-83f1-200c8071b925', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(704, '452ef92a-edae-4328-83f1-200c8071b925', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(705, '452ef92a-edae-4328-83f1-200c8071b925', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(706, '452ef92a-edae-4328-83f1-200c8071b925', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(707, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 2, 'Executive Summary: InsideOut is an innovative AI-based anti-plagiarism platform designed to combat plagiarism in educational institutions', 0, 34.7912, 65.2088, 'text-davinci-002', '{\"GLM130B\": 17.189572751522064, \"mixtral-8x7b\": 2.6393288746476173, \"t0_11b\": 4.0702201426029205, \"text-davinci-002\": 17.61145442724228, \"text-davinci-003\": 10.206353664398193}', 65.2088),
(708, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 3, 'Our main objective is to maximize creativity and foster a sense of academic inquiry among students, thus promoting an honest and ethical learning environment', 0, 26.7912, 73.2088, 'gpt-3.5-turbo', '{\"gpt-3.5-turbo\": 35.59751510620117, \"t0_11b\": 6.153709068894386, \"t0_3b\": 3.5969678312540054, \"text-davinci-002\": 8.487856388092041, \"text-davinci-003\": 5.080416798591614}', 73.2088),
(709, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 4, 'The platform provides a number of unique features including cross-institutional plagiarism analysis of text and image content, detection of text generated by ChatGPT and other generative artificial intelligence, misspelling correction, web content search, and content similarity analysis', 0, 4.1347, 95.8653, 't0_11b', '{\"flan_t5_base\": 1.6046172007918358, \"flan_t5_large\": 2.8542449697852135, \"t0_11b\": 49.39051866531372, \"t0_3b\": 38.61706256866455}', 95.8653),
(710, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 7, 'Description of the Problem: Plagiarism is a growing problem in the educational field that affects both students and institutions', 0, 32.5515, 67.4485, 't0_11b', '{\"flan_t5_base\": 4.279111325740814, \"mixtral-8x7b\": 10.04665121436119, \"t0_11b\": 24.730731546878815, \"t0_3b\": 5.417586490511894, \"text-davinci-002\": 7.389088720083237}', 67.4485),
(711, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 8, 'The ease of access to information online has led to an increase in the unauthorized copying of academic work, which undermines the integrity of the educational process and impairs the development of students\' research and creative skills', 0, 0.266481, 99.7335, 't0_11b', '{\"flan_t5_large\": 3.681693598628044, \"opt_iml_max_1.3b\": 2.316890098154545, \"t0_11b\": 49.343547224998474, \"t0_3b\": 28.487905859947205, \"text-davinci-002\": 6.573188304901123}', 99.7335),
(712, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 9, 'Educational institutions need an effective and reliable solution to detect and prevent plagiarism in all its forms', 1, 63.9201, 36.0799, NULL, '{\"GLM130B\": 8.88151153922081, \"mixtral-8x7b\": 1.282153557986021, \"text-davinci-002\": 19.972364604473114, \"text-davinci-003\": 2.1296149119734764}', 63.9201),
(713, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 11, 'Solution: InsideOut offers a comprehensive and advanced solution to combat plagiarism in the educational field', 0, 17.1419, 82.8581, 'text-davinci-003', '{\"GLM130B\": 13.40470165014267, \"gpt-3.5-turbo\": 5.179885029792786, \"mixtral-8x7b\": 5.457092821598053, \"text-davinci-002\": 16.333551704883575, \"text-davinci-003\": 32.56323039531708}', 82.8581),
(714, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 12, 'Our platform uses cutting-edge artificial intelligence technologies to analyze and compare the content of academic papers, identifying similarities with other sources and detecting possible cases of plagiarism', 1, 59.5056, 40.4944, NULL, '{\"GLM130B\": 3.435087949037552, \"t0_11b\": 22.006650269031525, \"t0_3b\": 5.61041496694088, \"text-davinci-002\": 2.6990821585059166}', 59.5056),
(715, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 13, 'Some key features of our platform are: Closed Platform: Exclusive access for teachers, guaranteeing the confidentiality and security of student work', 1, 84.5385, 15.4615, NULL, '{\"GLM130B\": 2.055578865110874, \"t0_11b\": 2.185641787946224, \"text-davinci-002\": 4.045836254954338}', 84.5385);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(716, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 14, 'Plagiarism Analysis in Text and Image Content: Our technology is capable of detecting similarities in text and also in images, which provides greater precision in detecting unauthorized copies', 0, 17.4969, 82.5031, 't0_11b', '{\"flan_t5_base\": 6.495032459497452, \"flan_t5_large\": 6.5967366099357605, \"flan_t5_small\": 4.8472534865140915, \"t0_11b\": 32.95668363571167, \"t0_3b\": 12.875215709209442}', 82.5031),
(717, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 15, 'Detection of Text Generated by ChatGPT and Generative Artificial Intelligences: Our system is capable of identifying content generated by artificial intelligences, ensuring that students do not use text generation tools to plagiarize', 0, 5.43632, 94.5637, 't0_11b', '{\"flan_t5_base\": 19.314628839492798, \"flan_t5_large\": 11.790917068719864, \"flan_t5_small\": 18.37548017501831, \"t0_11b\": 21.08389586210251, \"t0_3b\": 18.47861558198929}', 94.5637),
(718, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 16, 'Misspelling Detection: In addition to detecting similarities, InsideOut also checks spelling to ensure that papers are original and well-written', 1, 73.6687, 26.3313, NULL, '{\"gpt-3.5-turbo\": 2.6648202911019325, \"t0_11b\": 5.883374810218811, \"t0_3b\": 2.075725793838501, \"text-davinci-002\": 1.7024783417582512, \"text-davinci-003\": 5.8012377470731735}', 73.6687),
(719, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 17, 'Search for Content on the Web: The platform performs an exhaustive search on the Internet to detect possible sources of plagiarism and provide detailed reports on the matches found', 1, 62.4909, 37.5091, NULL, '{\"flan_t5_base\": 2.192106656730175, \"flan_t5_large\": 2.660263143479824, \"t0_11b\": 11.364849656820297, \"t0_3b\": 7.287091016769409, \"text-davinci-002\": 2.0945167168974876}', 62.4909),
(720, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 18, 'Patent Similarity Analysis: For research projects with technical or scientific content, InsideOut includes comparison with patent databases, thus avoiding plagiarism of protected ideas', 1, 97.8795, 2.12049, NULL, '{}', 97.8795),
(721, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 20, 'Customer Experience: Our focus is on providing the best possible experience for our customers', 1, 50.0103, 49.9897, NULL, '{\"GLM130B\": 1.697506569325924, \"mixtral-8x7b\": 1.1426224373281002, \"t0_11b\": 1.7292225733399391, \"text-davinci-002\": 28.86699140071869, \"text-davinci-003\": 10.905804485082626}', 50.0103),
(722, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 21, 'By choosing InsideOut, users get: Intuitive and Easy-to-Use Platform: We designed the InsideOut interface to be accessible and friendly for all users, facilitating its use for both teachers and students', 0, 2.78419, 97.2158, 't0_11b', '{\"flan_t5_base\": 2.111664228141308, \"flan_t5_large\": 2.7485137805342674, \"flan_t5_small\": 2.590731717646122, \"t0_11b\": 44.29624080657959, \"t0_3b\": 33.054742217063904}', 97.2158),
(723, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 22, 'Security and Credibility of Stored Data: Data privacy and security are fundamental to us', 1, 67.9209, 32.0791, NULL, '{\"GLM130B\": 3.81806343793869, \"flan_t5_base\": 1.6611652448773384, \"t0_11b\": 5.668074265122414, \"t0_3b\": 2.6519715785980225, \"text-davinci-002\": 7.87830650806427}', 67.9209),
(724, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 23, 'We implement advanced security measures to ensure the protection of our clients\' confidential information', 0, 23.6684, 76.3316, 'gemma-7b-it', '{\"gemma-7b-it\": 26.38586461544037, \"mixtral-8x7b\": 5.387815460562706, \"t0_11b\": 3.7576675415039062, \"text-davinci-002\": 8.640476316213608, \"text-davinci-003\": 22.325773537158966}', 76.3316),
(725, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 24, 'Specialized Technical Support: Our highly trained technical support team is available to provide fast and efficient assistance in case of any technical questions or problems', 1, 67.8985, 32.1015, NULL, '{\"GLM130B\": 1.7315765842795372, \"flan_t5_large\": 1.5009776689112186, \"t0_11b\": 1.5083316713571548, \"text-davinci-002\": 3.854537010192871, \"text-davinci-003\": 6.691845506429672}', 67.8985),
(726, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 25, 'Regular Data Backup: We make regular backups of the data stored on the platform, ensuring the integrity and availability of the information at all times', 0, 35.0788, 64.9212, 'text-davinci-003', '{\"gpt-3.5-turbo\": 3.2395143061876297, \"mixtral-8x7b\": 3.2010111957788467, \"t0_11b\": 11.624302715063095, \"text-davinci-002\": 3.401462361216545, \"text-davinci-003\": 21.197418868541718}', 64.9212),
(727, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 26, 'Personalization and Flexibility: We understand that each educational institution is unique, which is why we offer the ability to customize the platform according to the needs and policies of each client', 0, 14.0477, 85.9523, 't0_11b', '{\"flan_t5_small\": 4.9144405871629715, \"t0_11b\": 28.912988305091858, \"t0_3b\": 18.495512008666992, \"text-davinci-002\": 7.851459830999374, \"text-davinci-003\": 6.970493495464325}', 85.9523),
(728, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 27, 'We also provide integration options with existing learning management systems for a seamless transition', 1, 93.3003, 6.69972, NULL, '{\"text-davinci-002\": 1.0723466984927654}', 93.3003),
(729, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 28, 'Advanced Report Analysis: Our platform offers detailed reports on detected plagiarism, allowing teachers and administrators to gain deep insight into student academic performance and integrity', 0, 36.8714, 63.1286, 'text-davinci-003', '{\"GLM130B\": 3.960046172142029, \"t0_11b\": 8.131694793701172, \"t0_3b\": 5.973988398909569, \"text-davinci-002\": 5.981653928756714, \"text-davinci-003\": 9.79878082871437}', 63.1286),
(730, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 29, 'Continuous Updates: We are committed to constantly improving InsideOut through updates and improvements based on feedback from our users and technological advances', 0, 42.5372, 57.4628, 't0_11b', '{\"flan_t5_base\": 2.3616431280970573, \"opt_13b\": 5.59544712305069, \"opt_iml_30b\": 2.5573261082172394, \"t0_11b\": 19.75000947713852, \"t0_3b\": 7.285204529762268}', 57.4628),
(731, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 31, 'Business Model: InsideOut will operate under a subscription model for educational institutions', 1, 91.9563, 8.04375, NULL, '{\"GLM130B\": 3.001341037452221, \"mixtral-8x7b\": 1.0399391874670982, \"text-davinci-002\": 1.5248077921569347}', 91.9563),
(732, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 1, 32, 'We will offer different plans depending on the size of the institution and the frequency of use of the platform', 1, 91.2909, 8.70912, NULL, '{\"flan_t5_small\": 1.155210193246603, \"t0_11b\": 2.4119162932038307, \"t0_3b\": 1.2752223759889603}', 91.2909),
(733, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 1, 'will offer customized versions for those institutions that wish to integrate InsideOut with their existing learning management systems', 1, 95.6812, 4.31884, NULL, '{\"text-davinci-002\": 1.7887072637677193}', 95.6812),
(734, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 2, 'We will also explore the possibility of offering individual plans for students who wish to verify their work before submitting it', 1, 50.8838, 49.1162, NULL, '{\"bloomz\": 5.97538985311985, \"mixtral-8x7b\": 2.6466546580195427, \"t0_11b\": 8.890213817358017, \"t0_3b\": 7.22789466381073, \"text-davinci-002\": 8.18437859416008}', 50.8838),
(735, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 4, 'Future Vision: Our vision is to make InsideOut the world\'s leading solution to combat plagiarism in educational institutions', 0, 38.3778, 61.6222, 'text-davinci-002', '{\"GLM130B\": 8.547049760818481, \"t0_11b\": 7.936743646860123, \"t0_3b\": 2.687281370162964, \"text-davinci-002\": 23.24804663658142, \"text-davinci-003\": 2.6593580842018127}', 61.6222),
(736, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 5, 'We aspire to be recognized as the gold standard in academic integrity, thereby helping to foster genuine inquiry and creativity in future generations of students', 0, 20.0697, 79.9303, 'gpt-3.5-turbo', '{\"gemma-7b-it\": 8.667504787445068, \"gpt-3.5-turbo\": 18.802092969417572, \"llama3-70b\": 6.971973925828934, \"llama3-8b\": 7.694951444864273, \"t0_11b\": 13.913755118846893}', 79.9303),
(737, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 6, 'In the future, we plan to expand our presence internationally and collaborate with educational and government organizations to promote academic integrity on a global scale', 0, 13.6667, 86.3333, 't0_11b', '{\"flan_t5_base\": 4.916928336024284, \"flan_t5_large\": 4.35618944466114, \"flan_t5_small\": 3.1140193343162537, \"t0_11b\": 43.71527135372162, \"t0_3b\": 25.554487109184265}', 86.3333),
(738, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 8, 'Future Innovations: In our commitment to continue to be a leader in the field of academic integrity, we are planning to implement the following innovations in the future: Multimodal Analysis: We will improve our platform so that it can analyze not only text and images, but also content in more complex formats, such as videos and presentations, thus extending plagiarism detection to new forms of academic presentation', 1, 62.2276, 37.7724, NULL, '{\"opt_2.7b\": 2.3746097460389137, \"opt_30b\": 2.2592948749661446, \"opt_6.7b\": 3.5849109292030334, \"opt_iml_30b\": 13.941952586174011, \"opt_iml_max_1.3b\": 9.568029642105103}', 62.2276),
(739, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 9, 'Paraphrase Identification: We will develop advanced techniques to detect paraphrases and rewriting of texts, which will allow us to identify more sophisticated and subtle cases of plagiarism', 0, 5.38276, 94.6172, 't0_11b', '{\"flan_t5_base\": 7.789625972509384, \"flan_t5_large\": 6.5559931099414825, \"flan_t5_small\": 6.732261925935745, \"t0_11b\": 39.389920234680176, \"t0_3b\": 24.289600551128387}', 94.6172),
(740, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 10, 'Integration with Conversational Artificial Intelligence: We will take advantage of the capabilities of conversational artificial intelligence to improve the user experience, allowing teachers to interact with the platform and obtain results faster', 0, 2.44282, 97.5572, 't0_11b', '{\"flan_t5_base\": 4.838467016816139, \"flan_t5_large\": 3.8294803351163864, \"flan_t5_small\": 5.2231717854738235, \"t0_11b\": 44.13602352142334, \"t0_3b\": 28.322163224220276}', 97.5572),
(741, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 11, 'Media Content Analysis: We will implement media analysis recognition technologies to detect plagiarism in recorded speech and live broadcast content, thus addressing new forms of unauthorized copying', 0, 16.1308, 83.8692, 't0_11b', '{\"flan_t5_base\": 9.361135959625244, \"flan_t5_large\": 8.757440000772476, \"flan_t5_small\": 7.2495609521865845, \"t0_11b\": 24.598436057567596, \"t0_3b\": 17.43338257074356}', 83.8692),
(742, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 12, 'Generative Adversarial Neural Networks (GANs): We will investigate the use of GANs to help students prevent plagiarism from the stage of creating academic papers', 0, 6.83418, 93.1658, 't0_11b', '{\"flan_t5_base\": 10.402149707078934, \"flan_t5_large\": 4.183986410498619, \"flan_t5_small\": 3.9208736270666122, \"t0_11b\": 37.08020746707916, \"t0_3b\": 28.949549794197083}', 93.1658),
(743, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 14, 'Conclusions: InsideOut is positioned as the most advanced and reliable anti-plagiarism platform on the market', 1, 79.5706, 20.4294, NULL, '{\"GLM130B\": 5.401511117815971, \"t0_11b\": 1.0953069664537907, \"text-davinci-002\": 5.5885422974824905, \"text-davinci-003\": 3.899930790066719}', 79.5706),
(744, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 15, 'Our focus on plagiarism detection in various types of content and backed by an exceptional customer experience set us apart from other solutions available', 1, 91.6106, 8.38936, NULL, '{\"GLM130B\": 1.2019029818475246, \"opt_13b\": 1.9402652978897095}', 91.6106),
(745, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 16, 'With InsideOut, educational institutions can guarantee the originality and authenticity of their students\' work, promoting an ethical and nurturing learning environment', 0, 35.3269, 64.6731, 'text-davinci-003', '{\"gemma-7b-it\": 8.96531343460083, \"gpt-3.5-turbo\": 16.732025146484375, \"llama3-8b\": 5.431848764419556, \"text-davinci-002\": 4.360374808311462, \"text-davinci-003\": 17.930257320404053}', 64.6731),
(746, '7259f522-d8bf-49c5-8102-2c41128f0cb5', 2, 17, 'We look to the future with enthusiasm, committed to continuing to develop innovative technologies that protect academic integrity and foster creativity in the world of education', 0, 4.54033, 95.4597, 't0_11b', '{\"flan_t5_base\": 3.2098721712827682, \"flan_t5_large\": 5.282832682132721, \"t0_11b\": 45.47313749790192, \"t0_3b\": 19.274163246154785, \"text-davinci-002\": 4.117799177765846}', 95.4597),
(747, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(748, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(749, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(750, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(751, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(752, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(753, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(754, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(755, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(756, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(757, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(758, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(759, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(760, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(761, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(762, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(763, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(764, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(765, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(766, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(767, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(768, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(769, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(770, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(771, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(772, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(773, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(774, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(775, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(776, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(777, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(778, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(779, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(780, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(781, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(782, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(783, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(784, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(785, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(786, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(787, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(788, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(789, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(790, '47575483-666c-471b-9074-d6d1504a8249', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(791, '47575483-666c-471b-9074-d6d1504a8249', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(792, '47575483-666c-471b-9074-d6d1504a8249', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(793, '47575483-666c-471b-9074-d6d1504a8249', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(794, '47575483-666c-471b-9074-d6d1504a8249', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(795, '47575483-666c-471b-9074-d6d1504a8249', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(796, '47575483-666c-471b-9074-d6d1504a8249', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(797, '47575483-666c-471b-9074-d6d1504a8249', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(798, '47575483-666c-471b-9074-d6d1504a8249', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(799, '47575483-666c-471b-9074-d6d1504a8249', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(800, '47575483-666c-471b-9074-d6d1504a8249', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(801, '47575483-666c-471b-9074-d6d1504a8249', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(802, '47575483-666c-471b-9074-d6d1504a8249', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(803, '47575483-666c-471b-9074-d6d1504a8249', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(804, '47575483-666c-471b-9074-d6d1504a8249', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(805, '47575483-666c-471b-9074-d6d1504a8249', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(806, '47575483-666c-471b-9074-d6d1504a8249', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(807, '47575483-666c-471b-9074-d6d1504a8249', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(808, '47575483-666c-471b-9074-d6d1504a8249', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(809, '47575483-666c-471b-9074-d6d1504a8249', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(810, '47575483-666c-471b-9074-d6d1504a8249', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(811, '47575483-666c-471b-9074-d6d1504a8249', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(812, '47575483-666c-471b-9074-d6d1504a8249', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(813, '47575483-666c-471b-9074-d6d1504a8249', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(814, '47575483-666c-471b-9074-d6d1504a8249', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(815, '47575483-666c-471b-9074-d6d1504a8249', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(816, '47575483-666c-471b-9074-d6d1504a8249', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(817, '47575483-666c-471b-9074-d6d1504a8249', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(818, '47575483-666c-471b-9074-d6d1504a8249', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(819, '47575483-666c-471b-9074-d6d1504a8249', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(820, '47575483-666c-471b-9074-d6d1504a8249', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(821, '47575483-666c-471b-9074-d6d1504a8249', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(822, '47575483-666c-471b-9074-d6d1504a8249', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(823, '47575483-666c-471b-9074-d6d1504a8249', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(824, '47575483-666c-471b-9074-d6d1504a8249', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(825, '47575483-666c-471b-9074-d6d1504a8249', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(826, '47575483-666c-471b-9074-d6d1504a8249', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(827, '47575483-666c-471b-9074-d6d1504a8249', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(828, '47575483-666c-471b-9074-d6d1504a8249', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(829, '47575483-666c-471b-9074-d6d1504a8249', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(830, '47575483-666c-471b-9074-d6d1504a8249', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(831, '47575483-666c-471b-9074-d6d1504a8249', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(832, '47575483-666c-471b-9074-d6d1504a8249', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(833, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(834, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(835, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(836, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(837, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(838, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(839, '898bea33-438e-4385-aabc-3992be58c7ac', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(840, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(841, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(842, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(843, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(844, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(845, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(846, '898bea33-438e-4385-aabc-3992be58c7ac', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(847, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(848, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(849, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(850, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(851, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(852, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(853, '898bea33-438e-4385-aabc-3992be58c7ac', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(854, '898bea33-438e-4385-aabc-3992be58c7ac', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(855, '898bea33-438e-4385-aabc-3992be58c7ac', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(856, '898bea33-438e-4385-aabc-3992be58c7ac', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(857, '898bea33-438e-4385-aabc-3992be58c7ac', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252);
INSERT INTO `classified_paragraphs` (`id`, `analysis_id`, `page_number`, `paragraph_number`, `text`, `is_human`, `human_probability`, `ai_probability`, `predicted_model`, `model_scores`, `final_confidence`) VALUES
(858, '898bea33-438e-4385-aabc-3992be58c7ac', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(859, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(860, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(861, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(862, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(863, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(864, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(865, '898bea33-438e-4385-aabc-3992be58c7ac', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(866, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(867, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(868, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(869, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(870, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(871, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(872, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(873, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(874, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(875, '898bea33-438e-4385-aabc-3992be58c7ac', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(876, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 2, 'Executive Summary: InsideOut is an innovative AI-based anti-plagiarism platform designed to combat plagiarism in educational institutions', 0, 34.7912, 65.2088, 'text-davinci-002', '{\"GLM130B\": 17.189572751522064, \"mixtral-8x7b\": 2.6393288746476173, \"t0_11b\": 4.0702201426029205, \"text-davinci-002\": 17.61145442724228, \"text-davinci-003\": 10.206353664398193}', 65.2088),
(877, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 3, 'Our main objective is to maximize creativity and foster a sense of academic inquiry among students, thus promoting an honest and ethical learning environment', 0, 26.7912, 73.2088, 'gpt-3.5-turbo', '{\"gpt-3.5-turbo\": 35.59751510620117, \"t0_11b\": 6.153709068894386, \"t0_3b\": 3.5969678312540054, \"text-davinci-002\": 8.487856388092041, \"text-davinci-003\": 5.080416798591614}', 73.2088),
(878, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 4, 'The platform provides a number of unique features including cross-institutional plagiarism analysis of text and image content, detection of text generated by ChatGPT and other generative artificial intelligence, misspelling correction, web content search, and content similarity analysis', 0, 4.1347, 95.8653, 't0_11b', '{\"flan_t5_base\": 1.6046172007918358, \"flan_t5_large\": 2.8542449697852135, \"t0_11b\": 49.39051866531372, \"t0_3b\": 38.61706256866455}', 95.8653),
(879, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 7, 'Description of the Problem: Plagiarism is a growing problem in the educational field that affects both students and institutions', 0, 32.5515, 67.4485, 't0_11b', '{\"flan_t5_base\": 4.279111325740814, \"mixtral-8x7b\": 10.04665121436119, \"t0_11b\": 24.730731546878815, \"t0_3b\": 5.417586490511894, \"text-davinci-002\": 7.389088720083237}', 67.4485),
(880, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 8, 'The ease of access to information online has led to an increase in the unauthorized copying of academic work, which undermines the integrity of the educational process and impairs the development of students\' research and creative skills', 0, 0.266481, 99.7335, 't0_11b', '{\"flan_t5_large\": 3.681693598628044, \"opt_iml_max_1.3b\": 2.316890098154545, \"t0_11b\": 49.343547224998474, \"t0_3b\": 28.487905859947205, \"text-davinci-002\": 6.573188304901123}', 99.7335),
(881, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 9, 'Educational institutions need an effective and reliable solution to detect and prevent plagiarism in all its forms', 1, 63.9201, 36.0799, NULL, '{\"GLM130B\": 8.88151153922081, \"mixtral-8x7b\": 1.282153557986021, \"text-davinci-002\": 19.972364604473114, \"text-davinci-003\": 2.1296149119734764}', 63.9201),
(882, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 11, 'Solution: InsideOut offers a comprehensive and advanced solution to combat plagiarism in the educational field', 0, 17.1419, 82.8581, 'text-davinci-003', '{\"GLM130B\": 13.40470165014267, \"gpt-3.5-turbo\": 5.179885029792786, \"mixtral-8x7b\": 5.457092821598053, \"text-davinci-002\": 16.333551704883575, \"text-davinci-003\": 32.56323039531708}', 82.8581),
(883, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 12, 'Our platform uses cutting-edge artificial intelligence technologies to analyze and compare the content of academic papers, identifying similarities with other sources and detecting possible cases of plagiarism', 1, 59.5056, 40.4944, NULL, '{\"GLM130B\": 3.435087949037552, \"t0_11b\": 22.006650269031525, \"t0_3b\": 5.61041496694088, \"text-davinci-002\": 2.6990821585059166}', 59.5056),
(884, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 13, 'Some key features of our platform are: Closed Platform: Exclusive access for teachers, guaranteeing the confidentiality and security of student work', 1, 84.5385, 15.4615, NULL, '{\"GLM130B\": 2.055578865110874, \"t0_11b\": 2.185641787946224, \"text-davinci-002\": 4.045836254954338}', 84.5385),
(885, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 14, 'Plagiarism Analysis in Text and Image Content: Our technology is capable of detecting similarities in text and also in images, which provides greater precision in detecting unauthorized copies', 0, 17.4969, 82.5031, 't0_11b', '{\"flan_t5_base\": 6.495032459497452, \"flan_t5_large\": 6.5967366099357605, \"flan_t5_small\": 4.8472534865140915, \"t0_11b\": 32.95668363571167, \"t0_3b\": 12.875215709209442}', 82.5031),
(886, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 15, 'Detection of Text Generated by ChatGPT and Generative Artificial Intelligences: Our system is capable of identifying content generated by artificial intelligences, ensuring that students do not use text generation tools to plagiarize', 0, 5.43632, 94.5637, 't0_11b', '{\"flan_t5_base\": 19.314628839492798, \"flan_t5_large\": 11.790917068719864, \"flan_t5_small\": 18.37548017501831, \"t0_11b\": 21.08389586210251, \"t0_3b\": 18.47861558198929}', 94.5637),
(887, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 16, 'Misspelling Detection: In addition to detecting similarities, InsideOut also checks spelling to ensure that papers are original and well-written', 1, 73.6687, 26.3313, NULL, '{\"gpt-3.5-turbo\": 2.6648202911019325, \"t0_11b\": 5.883374810218811, \"t0_3b\": 2.075725793838501, \"text-davinci-002\": 1.7024783417582512, \"text-davinci-003\": 5.8012377470731735}', 73.6687),
(888, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 17, 'Search for Content on the Web: The platform performs an exhaustive search on the Internet to detect possible sources of plagiarism and provide detailed reports on the matches found', 1, 62.4909, 37.5091, NULL, '{\"flan_t5_base\": 2.192106656730175, \"flan_t5_large\": 2.660263143479824, \"t0_11b\": 11.364849656820297, \"t0_3b\": 7.287091016769409, \"text-davinci-002\": 2.0945167168974876}', 62.4909),
(889, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 18, 'Patent Similarity Analysis: For research projects with technical or scientific content, InsideOut includes comparison with patent databases, thus avoiding plagiarism of protected ideas', 1, 97.8795, 2.12049, NULL, '{}', 97.8795),
(890, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 20, 'Customer Experience: Our focus is on providing the best possible experience for our customers', 1, 50.0103, 49.9897, NULL, '{\"GLM130B\": 1.697506569325924, \"mixtral-8x7b\": 1.1426224373281002, \"t0_11b\": 1.7292225733399391, \"text-davinci-002\": 28.86699140071869, \"text-davinci-003\": 10.905804485082626}', 50.0103),
(891, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 21, 'By choosing InsideOut, users get: Intuitive and Easy-to-Use Platform: We designed the InsideOut interface to be accessible and friendly for all users, facilitating its use for both teachers and students', 0, 2.78419, 97.2158, 't0_11b', '{\"flan_t5_base\": 2.111664228141308, \"flan_t5_large\": 2.7485137805342674, \"flan_t5_small\": 2.590731717646122, \"t0_11b\": 44.29624080657959, \"t0_3b\": 33.054742217063904}', 97.2158),
(892, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 22, 'Security and Credibility of Stored Data: Data privacy and security are fundamental to us', 1, 67.9209, 32.0791, NULL, '{\"GLM130B\": 3.81806343793869, \"flan_t5_base\": 1.6611652448773384, \"t0_11b\": 5.668074265122414, \"t0_3b\": 2.6519715785980225, \"text-davinci-002\": 7.87830650806427}', 67.9209),
(893, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 23, 'We implement advanced security measures to ensure the protection of our clients\' confidential information', 0, 23.6684, 76.3316, 'gemma-7b-it', '{\"gemma-7b-it\": 26.38586461544037, \"mixtral-8x7b\": 5.387815460562706, \"t0_11b\": 3.7576675415039062, \"text-davinci-002\": 8.640476316213608, \"text-davinci-003\": 22.325773537158966}', 76.3316),
(894, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 24, 'Specialized Technical Support: Our highly trained technical support team is available to provide fast and efficient assistance in case of any technical questions or problems', 1, 67.8985, 32.1015, NULL, '{\"GLM130B\": 1.7315765842795372, \"flan_t5_large\": 1.5009776689112186, \"t0_11b\": 1.5083316713571548, \"text-davinci-002\": 3.854537010192871, \"text-davinci-003\": 6.691845506429672}', 67.8985),
(895, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 25, 'Regular Data Backup: We make regular backups of the data stored on the platform, ensuring the integrity and availability of the information at all times', 0, 35.0788, 64.9212, 'text-davinci-003', '{\"gpt-3.5-turbo\": 3.2395143061876297, \"mixtral-8x7b\": 3.2010111957788467, \"t0_11b\": 11.624302715063095, \"text-davinci-002\": 3.401462361216545, \"text-davinci-003\": 21.197418868541718}', 64.9212),
(896, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 26, 'Personalization and Flexibility: We understand that each educational institution is unique, which is why we offer the ability to customize the platform according to the needs and policies of each client', 0, 14.0477, 85.9523, 't0_11b', '{\"flan_t5_small\": 4.9144405871629715, \"t0_11b\": 28.912988305091858, \"t0_3b\": 18.495512008666992, \"text-davinci-002\": 7.851459830999374, \"text-davinci-003\": 6.970493495464325}', 85.9523),
(897, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 27, 'We also provide integration options with existing learning management systems for a seamless transition', 1, 93.3003, 6.69972, NULL, '{\"text-davinci-002\": 1.0723466984927654}', 93.3003),
(898, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 28, 'Advanced Report Analysis: Our platform offers detailed reports on detected plagiarism, allowing teachers and administrators to gain deep insight into student academic performance and integrity', 0, 36.8714, 63.1286, 'text-davinci-003', '{\"GLM130B\": 3.960046172142029, \"t0_11b\": 8.131694793701172, \"t0_3b\": 5.973988398909569, \"text-davinci-002\": 5.981653928756714, \"text-davinci-003\": 9.79878082871437}', 63.1286),
(899, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 29, 'Continuous Updates: We are committed to constantly improving InsideOut through updates and improvements based on feedback from our users and technological advances', 0, 42.5372, 57.4628, 't0_11b', '{\"flan_t5_base\": 2.3616431280970573, \"opt_13b\": 5.59544712305069, \"opt_iml_30b\": 2.5573261082172394, \"t0_11b\": 19.75000947713852, \"t0_3b\": 7.285204529762268}', 57.4628),
(900, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 31, 'Business Model: InsideOut will operate under a subscription model for educational institutions', 1, 91.9563, 8.04375, NULL, '{\"GLM130B\": 3.001341037452221, \"mixtral-8x7b\": 1.0399391874670982, \"text-davinci-002\": 1.5248077921569347}', 91.9563),
(901, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 1, 32, 'We will offer different plans depending on the size of the institution and the frequency of use of the platform', 1, 91.2909, 8.70912, NULL, '{\"flan_t5_small\": 1.155210193246603, \"t0_11b\": 2.4119162932038307, \"t0_3b\": 1.2752223759889603}', 91.2909),
(902, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 1, 'will offer customized versions for those institutions that wish to integrate InsideOut with their existing learning management systems', 1, 95.6812, 4.31884, NULL, '{\"text-davinci-002\": 1.7887072637677193}', 95.6812),
(903, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 2, 'We will also explore the possibility of offering individual plans for students who wish to verify their work before submitting it', 1, 50.8838, 49.1162, NULL, '{\"bloomz\": 5.97538985311985, \"mixtral-8x7b\": 2.6466546580195427, \"t0_11b\": 8.890213817358017, \"t0_3b\": 7.22789466381073, \"text-davinci-002\": 8.18437859416008}', 50.8838),
(904, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 4, 'Future Vision: Our vision is to make InsideOut the world\'s leading solution to combat plagiarism in educational institutions', 0, 38.3778, 61.6222, 'text-davinci-002', '{\"GLM130B\": 8.547049760818481, \"t0_11b\": 7.936743646860123, \"t0_3b\": 2.687281370162964, \"text-davinci-002\": 23.24804663658142, \"text-davinci-003\": 2.6593580842018127}', 61.6222),
(905, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 5, 'We aspire to be recognized as the gold standard in academic integrity, thereby helping to foster genuine inquiry and creativity in future generations of students', 0, 20.0697, 79.9303, 'gpt-3.5-turbo', '{\"gemma-7b-it\": 8.667504787445068, \"gpt-3.5-turbo\": 18.802092969417572, \"llama3-70b\": 6.971973925828934, \"llama3-8b\": 7.694951444864273, \"t0_11b\": 13.913755118846893}', 79.9303),
(906, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 6, 'In the future, we plan to expand our presence internationally and collaborate with educational and government organizations to promote academic integrity on a global scale', 0, 13.6667, 86.3333, 't0_11b', '{\"flan_t5_base\": 4.916928336024284, \"flan_t5_large\": 4.35618944466114, \"flan_t5_small\": 3.1140193343162537, \"t0_11b\": 43.71527135372162, \"t0_3b\": 25.554487109184265}', 86.3333),
(907, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 8, 'Future Innovations: In our commitment to continue to be a leader in the field of academic integrity, we are planning to implement the following innovations in the future: Multimodal Analysis: We will improve our platform so that it can analyze not only text and images, but also content in more complex formats, such as videos and presentations, thus extending plagiarism detection to new forms of academic presentation', 1, 62.2276, 37.7724, NULL, '{\"opt_2.7b\": 2.3746097460389137, \"opt_30b\": 2.2592948749661446, \"opt_6.7b\": 3.5849109292030334, \"opt_iml_30b\": 13.941952586174011, \"opt_iml_max_1.3b\": 9.568029642105103}', 62.2276),
(908, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 9, 'Paraphrase Identification: We will develop advanced techniques to detect paraphrases and rewriting of texts, which will allow us to identify more sophisticated and subtle cases of plagiarism', 0, 5.38276, 94.6172, 't0_11b', '{\"flan_t5_base\": 7.789625972509384, \"flan_t5_large\": 6.5559931099414825, \"flan_t5_small\": 6.732261925935745, \"t0_11b\": 39.389920234680176, \"t0_3b\": 24.289600551128387}', 94.6172),
(909, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 10, 'Integration with Conversational Artificial Intelligence: We will take advantage of the capabilities of conversational artificial intelligence to improve the user experience, allowing teachers to interact with the platform and obtain results faster', 0, 2.44282, 97.5572, 't0_11b', '{\"flan_t5_base\": 4.838467016816139, \"flan_t5_large\": 3.8294803351163864, \"flan_t5_small\": 5.2231717854738235, \"t0_11b\": 44.13602352142334, \"t0_3b\": 28.322163224220276}', 97.5572),
(910, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 11, 'Media Content Analysis: We will implement media analysis recognition technologies to detect plagiarism in recorded speech and live broadcast content, thus addressing new forms of unauthorized copying', 0, 16.1308, 83.8692, 't0_11b', '{\"flan_t5_base\": 9.361135959625244, \"flan_t5_large\": 8.757440000772476, \"flan_t5_small\": 7.2495609521865845, \"t0_11b\": 24.598436057567596, \"t0_3b\": 17.43338257074356}', 83.8692),
(911, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 12, 'Generative Adversarial Neural Networks (GANs): We will investigate the use of GANs to help students prevent plagiarism from the stage of creating academic papers', 0, 6.83418, 93.1658, 't0_11b', '{\"flan_t5_base\": 10.402149707078934, \"flan_t5_large\": 4.183986410498619, \"flan_t5_small\": 3.9208736270666122, \"t0_11b\": 37.08020746707916, \"t0_3b\": 28.949549794197083}', 93.1658),
(912, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 14, 'Conclusions: InsideOut is positioned as the most advanced and reliable anti-plagiarism platform on the market', 1, 79.5706, 20.4294, NULL, '{\"GLM130B\": 5.401511117815971, \"t0_11b\": 1.0953069664537907, \"text-davinci-002\": 5.5885422974824905, \"text-davinci-003\": 3.899930790066719}', 79.5706),
(913, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 15, 'Our focus on plagiarism detection in various types of content and backed by an exceptional customer experience set us apart from other solutions available', 1, 91.6106, 8.38936, NULL, '{\"GLM130B\": 1.2019029818475246, \"opt_13b\": 1.9402652978897095}', 91.6106),
(914, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 16, 'With InsideOut, educational institutions can guarantee the originality and authenticity of their students\' work, promoting an ethical and nurturing learning environment', 0, 35.3269, 64.6731, 'text-davinci-003', '{\"gemma-7b-it\": 8.96531343460083, \"gpt-3.5-turbo\": 16.732025146484375, \"llama3-8b\": 5.431848764419556, \"text-davinci-002\": 4.360374808311462, \"text-davinci-003\": 17.930257320404053}', 64.6731),
(915, 'a7c51044-52ce-4ce4-b204-21bd344803d5', 2, 17, 'We look to the future with enthusiasm, committed to continuing to develop innovative technologies that protect academic integrity and foster creativity in the world of education', 0, 4.54033, 95.4597, 't0_11b', '{\"flan_t5_base\": 3.2098721712827682, \"flan_t5_large\": 5.282832682132721, \"t0_11b\": 45.47313749790192, \"t0_3b\": 19.274163246154785, \"text-davinci-002\": 4.117799177765846}', 95.4597),
(916, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for  High-Performance Data Compression​ Author: Ruben Eduardo Gonzalez Nova​ Affiliation: Uryx Technologies SRL Dominican Republic​ Email: rgonzalez@uryxtech', 0, 34.7118, 65.2882, 'bloomz', '{\"bloomz\": 26.92032754421234, \"gpt_neox\": 4.0639713406562805, \"opt_13b\": 4.617441818118095, \"opt_iml_30b\": 2.060556598007679, \"text-davinci-002\": 4.200729727745056}', 65.2882),
(917, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 2, 'com   Abstract  This paper presents Fractal-ANS, a novel lossless compression algorithm that  synergizes fractal geometry with asymmetric numeral systems (ANS) to achieve  unprecedented compression efficiency', 0, 9.54304, 90.457, 't0_11b', '{\"GLM130B\": 2.8748849406838417, \"flan_t5_large\": 3.34073044359684, \"opt_iml_30b\": 3.227026015520096, \"t0_11b\": 35.220733284950256, \"t0_3b\": 28.22156250476837}', 90.457),
(918, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 3, 'The algorithm introduces a two-stage  process: (1) fractal pattern recognition using an optimized Collage Theorem  implementation to identify multi-scale redundancies, and (2) context-aware ANS  encoding with hardware-specific optimizations', 0, 2.5933, 97.4067, 't0_11b', '{\"flan_t5_base\": 10.944663733243942, \"flan_t5_large\": 15.407709777355194, \"flan_t5_small\": 10.85658147931099, \"t0_11b\": 29.282236099243164, \"t0_3b\": 26.561537384986877}', 97.4067),
(919, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 4, 'Fractal-ANS operates in two  variants: Ultra (leveraging GPU tensor cores for 24 GB/s throughput) and Lite  (CPU-optimized with AVX-512 for 5', 0, 15.1773, 84.8227, 't0_3b', '{\"flan_t5_base\": 9.041106700897217, \"flan_t5_large\": 5.96570260822773, \"flan_t5_small\": 11.490023136138916, \"t0_11b\": 19.112177193164825, \"t0_3b\": 28.727829456329346}', 84.8227),
(920, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 6, 'Evaluations on heterogeneous datasets  demonstrate a 28–38% improvement in compression density over Zstandard and  Brotli, while maintaining linear scalability', 1, 93.9643, 6.0357, NULL, '{}', 93.9643),
(921, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 7, 'Theoretical analysis confirms subquadratic  time complexity  O(nlog⁡n), outperforming existing fractal-based methods by 40%', 1, 93.868, 6.13197, NULL, '{\"GLM130B\": 1.036620419472456}', 93.868),
(922, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 1, 8, 'Keywords: Fractal compression, ANS coding, GPU acceleration, entropy reduction,  parallel algorithms', 1, 82.0328, 17.9672, NULL, '{\"GLM130B\": 1.356593519449234, \"flan_t5_base\": 1.189799327403307, \"t0_11b\": 4.408599063754082, \"text-davinci-002\": 2.556147985160351, \"text-davinci-003\": 1.131805032491684}', 82.0328),
(923, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 4, ', genomic sequencing, 4K  video streaming) demands compression algorithms that transcend traditional  entropy-based approaches', 1, 69.8732, 30.1268, NULL, '{\"GLM130B\": 2.382075786590576, \"flan_t5_base\": 6.268932670354843, \"flan_t5_large\": 5.623156949877739, \"t0_11b\": 2.0161833614110947, \"t0_3b\": 3.417747840285301}', 69.8732),
(924, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 6, '​ Local Redundancy Focus: LZ-family algorithms fail to detect global fractal  patterns', 1, 86.3478, 13.6522, NULL, '{\"GLM130B\": 3.242631256580353, \"mixtral-8x7b\": 2.216070331633091, \"text-davinci-002\": 2.000226639211178}', 86.3478),
(925, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 8, '​ Static Context Modeling: ANS implementations lack dynamic adaptation to  data topology', 1, 82.9429, 17.0571, NULL, '{\"GLM130B\": 2.7367601171135902, \"flan_t5_base\": 2.023795060813427, \"llama3-70b\": 1.2859591282904148, \"mixtral-8x7b\": 2.7671942487359047}', 82.9429),
(926, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 10, '​ Hardware Underutilization: Existing methods do not fully exploit GPU tensor  cores or CPU SIMD', 1, 74.5109, 25.4891, NULL, '{\"GLM130B\": 4.061463847756386, \"llama3-70b\": 2.369111031293869, \"llama3-8b\": 1.094252709299326, \"mixtral-8x7b\": 5.901269242167473, \"text-davinci-002\": 2.67699658870697}', 74.5109),
(927, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 11, 'Fractal-ANS addresses these gaps through:   ●​ Multi-Scale Fractal Segmentation: Identifying self-similar patterns via affine  transformations', 1, 75.4867, 24.5133, NULL, '{\"GLM130B\": 2.8434447944164276, \"mixtral-8x7b\": 14.12988156080246}', 75.4867),
(928, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 12, '●​ Adaptive ANS Contexts: Dynamically adjusting symbol probabilities based on  fractal structure', 1, 83.2824, 16.7176, NULL, '{\"llama3-8b\": 1.3677139766514301, \"mixtral-8x7b\": 10.723137110471725}', 83.2824),
(929, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 2, 13, '●​ Hardware-Aware Pipelines: GPU-optimized kernels (Ultra) and CPU  vectorization (Lite)', 1, 60.4951, 39.5049, NULL, '{\"GLM130B\": 2.588360197842121, \"gpt-3.5-turbo\": 1.6482703387737274, \"llama3-8b\": 3.9928052574396133, \"mixtral-8x7b\": 22.02392667531967, \"text-davinci-002\": 1.0009040124714375}', 60.4951),
(930, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 2, 'Related Work  Fractal Compression  Barnsley’s Iterated Function Systems (IFS) achieved 10,000:1 image compression  but suffered from O(n2)  complexity', 0, 45.6195, 54.3805, 't0_3b', '{\"flan_t5_base\": 5.547918006777763, \"flan_t5_large\": 2.5761233642697334, \"flan_t5_small\": 6.298235058784485, \"t0_11b\": 10.331972688436508, \"t0_3b\": 14.50851857662201}', 54.3805),
(931, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 4, 'Entropy Coding  ANS outperforms Huffman in compression ratio (15% avg', 1, 95.788, 4.21203, NULL, '{\"bloomz\": 1.2111249379813671, \"mixtral-8x7b\": 1.1752582155168056}', 95.788),
(932, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 6, 'Our work integrates fractal-derived contexts to reduce ANS table  redundancy by 60%', 1, 96.196, 3.80395, NULL, '{\"GLM130B\": 1.170136034488678, \"cohere\": 1.1074933223426342}', 96.196),
(933, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 7, 'Hardware Acceleration  CUDA-LZ77 achieves 8 GB/s on GPUs but ignores fractal patterns', 1, 95.9763, 4.02367, NULL, '{\"mixtral-8x7b\": 1.417913381010294}', 95.9763),
(934, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 8, 'Fractal-ANS Ultra  leverages tensor cores for fractal detection at 142 TFLOPS', 1, 58.8994, 41.1006, NULL, '{\"GLM130B\": 6.076990440487862, \"flan_t5_base\": 5.711911618709564, \"flan_t5_large\": 2.9075926169753075, \"mixtral-8x7b\": 7.322399318218231, \"t0_3b\": 3.436538949608803}', 58.8994),
(935, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 10, 'Methodology  Problem Formulation  For input D, compute compressed C(D) such that:                        min∣C(D)∣  s', 0, 47.2252, 52.7748, 'flan_t5_small', '{\"GLM130B\": 5.083351954817772, \"flan_t5_base\": 5.706915631890297, \"flan_t5_large\": 4.291329905390739, \"flan_t5_small\": 5.715882405638695, \"t0_11b\": 4.815128073096275}', 52.7748),
(936, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 3, 18, '​ Apply Collage Theorem to find affine transforms  wi (Bj)→Bk', 0, 43.6097, 56.3903, 'mixtral-8x7b', '{\"gemma-7b-it\": 16.435907781124115, \"gemma2-9b-it\": 1.0393016040325165, \"llama3-70b\": 3.6827262490987778, \"llama3-8b\": 1.6124794259667397, \"mixtral-8x7b\": 30.117526650428772}', 56.3903),
(937, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 4, 3, '​ Fractal Collage Optimization:    where W={wi} is the set of affine transforms and λ controls sparsity', 1, 70.754, 29.246, NULL, '{\"GLM130B\": 2.6725202798843384, \"flan_t5_base\": 2.5221824645996094, \"t0_11b\": 2.492438815534115, \"t0_3b\": 5.273719131946564, \"text-davinci-002\": 1.7489634454250336}', 70.754),
(938, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 5, 1, 'where  fctx  and Cctx  are frequency/cumulative functions from fractal context ctx', 1, 98.0199, 1.98011, NULL, '{}', 98.0199),
(939, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 6, 1, 'Setup  ●​ Hardware:  ○​ Ultra: NVIDIA H100 (80 GB VRAM), CUDA 12', 0, 15.7978, 84.2022, 'mixtral-8x7b', '{\"bloomz\": 4.488524422049522, \"llama3-70b\": 4.462304338812828, \"llama3-8b\": 7.706481218338013, \"mixtral-8x7b\": 62.818533182144165}', 84.2022),
(940, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 6, 3, '3  ●​ Datasets:  ○​ Text: Wikipedia XML (42 GB)  ○​ Media: 8K RAW video (1', 1, 73.5252, 26.4748, NULL, '{\"GLM130B\": 1.1691846884787083, \"bloomz\": 5.53566999733448, \"llama3-70b\": 1.4843206852674484, \"llama3-8b\": 1.628994382917881, \"mixtral-8x7b\": 12.567217648029327}', 73.5252),
(941, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 6, 4, '2 TB)  ○​ Scientific: Genomic FASTQ (650 GB)  Results    Figure 1: Compression Ratio vs', 1, 61.1103, 38.8897, NULL, '{\"bloomz\": 5.344167724251747, \"llama3-70b\": 2.1303819492459297, \"llama3-8b\": 1.2929466553032398, \"mixtral-8x7b\": 26.73434317111969}', 61.1103),
(942, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 1, '●​ Upper-right = Optimal region (low ratio + high speed)', 1, 93.0662, 6.93381, NULL, '{\"mixtral-8x7b\": 5.369703844189644}', 93.0662),
(943, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 4, 'This visualization highlights Fractal-ANS’s unique ability to break the traditional  speed/ratio trade-off via fractal pattern analysis', 0, 48.0344, 51.9656, 'gemma-7b-it', '{\"davinci\": 2.0728152245283127, \"gemma-7b-it\": 22.9029580950737, \"gemma2-9b-it\": 4.068472608923912, \"llama3-8b\": 2.7812624350190163, \"mixtral-8x7b\": 10.485956817865372}', 51.9656),
(944, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 5, '​  Table 2: Compression Efficiency by Dataset    Dataset  Fractal-ANS Ultra  Zstandard  Improvement  Wikipedia XML  18%  29%  38%  8K Video  22%  37%  41%  Genomic  25%  34%  26%   7', 0, 36.7749, 63.2251, 'bloomz', '{\"GLM130B\": 2.4749552831053734, \"bloomz\": 33.01075994968414, \"gemma-7b-it\": 2.9880598187446594, \"gpt_neox\": 3.676086664199829, \"mixtral-8x7b\": 7.0242345333099365}', 63.2251),
(945, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 6, 'Discussion  Advantages  ●​ Fractal Contexts: Reduce ANS table size by 60% vs', 1, 58.3086, 41.6914, NULL, '{\"bloomz\": 2.6600494980812073, \"llama3-70b\": 4.792438820004463, \"llama3-8b\": 2.190648764371872, \"mixtral-8x7b\": 27.87230908870697}', 58.3086),
(946, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 8, '●​ GPU Utilization: 92% tensor core occupancy in Ultra variant', 1, 57.2552, 42.7448, NULL, '{\"GLM130B\": 1.2081880122423172, \"gemma-7b-it\": 2.459557354450226, \"llama3-70b\": 1.7171381041407585, \"llama3-8b\": 3.2732099294662476, \"mixtral-8x7b\": 30.72906732559204}', 57.2552),
(947, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 11, 'Limitations  ●​ Memory Footprint: Ultra variant requires >8 GB VRAM for 1 TB datasets', 1, 92.1648, 7.83521, NULL, '{\"mixtral-8x7b\": 5.191006883978844}', 92.1648),
(948, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 7, 14, 'Applications  ●​ Medical Imaging: 3D MRI scans with fractal tumor patterns', 1, 93.6784, 6.32163, NULL, '{\"mixtral-8x7b\": 4.040810838341713}', 93.6784),
(949, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 1, 'Fractal-ANS establishes a new paradigm in lossless compression by unifying fractal  geometry with entropy coding', 0, 41.5667, 58.4333, 'mixtral-8x7b', '{\"GLM130B\": 3.5835016518831253, \"mixtral-8x7b\": 16.373153030872345, \"t0_11b\": 8.99573341012001, \"t0_3b\": 5.1064953207969666, \"text-davinci-002\": 4.828101396560669}', 58.4333),
(950, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 2, 'The Ultra variant achieves 24 GB/s throughput on  GPUs, while Lite maintains 5', 1, 97.7111, 2.28894, NULL, '{}', 97.7111),
(951, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 3, '2 GB/s on CPUs with 5× better compression than  Zstandard', 1, 97.2917, 2.70829, NULL, '{}', 97.2917),
(952, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 4, 'Future work includes quantum annealing for fractal optimization and DPU  offloading', 1, 96.1035, 3.89654, NULL, '{}', 96.1035),
(953, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 11, 'Duda, \"Asymmetric Numeral Systems: Entropy Coding Combined with  Statistical Modeling,\" IEEE Data Compression Conf', 0, 44.5271, 55.4729, 'mixtral-8x7b', '{\"GLM130B\": 4.214002192020416, \"flan_t5_base\": 1.9094401970505714, \"llama3-70b\": 6.938590109348297, \"mixtral-8x7b\": 24.903349578380585, \"t0_11b\": 1.873551867902279}', 55.4729),
(954, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 15, 'Collet, \"Zstandard: Fast and Efficient Compression Algorithm,\" Facebook  Engineering Blog, 2016', 0, 18.3246, 81.6754, 'mixtral-8x7b', '{\"GLM130B\": 8.072251826524734, \"gpt-3.5-turbo\": 5.539557337760925, \"llama3-70b\": 3.5670123994350433, \"mixtral-8x7b\": 38.384318351745605, \"text-davinci-002\": 3.3893752843141556}', 81.6754),
(955, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 19, 'com/fractal-ans/core  ●​ Data: Public datasets from Silesia Corpus and YouTube-8K', 1, 52.9068, 47.0932, NULL, '{\"bloomz\": 27.476918697357178, \"mixtral-8x7b\": 17.6675483584404}', 52.9068),
(956, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 23, 'GPU benchmarks were  conducted on dedicated infrastructure to avoid energy waste', 1, 76.1283, 23.8717, NULL, '{\"GLM130B\": 7.283339649438858, \"flan_t5_base\": 1.3481367379426956, \"flan_t5_large\": 2.4403775110840797, \"t0_11b\": 2.5444423779845238, \"t0_3b\": 2.6244863867759705}', 76.1283),
(957, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 24, 'This paper provides a comprehensive framework for next-generation compression  systems, validated through theoretical rigor and empirical evidence', 1, 53.655, 46.345, NULL, '{\"gemma-7b-it\": 2.350037731230259, \"gpt4\": 2.4717262014746666, \"opt_iml_30b\": 3.0881328508257866, \"t0_11b\": 14.869458973407745, \"t0_3b\": 9.023834019899368}', 53.655),
(958, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', 8, 25, 'The integration  of fractal mathematics with modern hardware capabilities opens new frontiers in  data engineering', 1, 57.6123, 42.3877, NULL, '{\"GLM130B\": 4.119269549846649, \"gemma-7b-it\": 3.420429304242134, \"t0_11b\": 7.890886813402176, \"t0_3b\": 10.172126442193985, \"text-davinci-002\": 5.747562274336815}', 57.6123),
(959, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 1, 'will offer customized versions for those institutions that wish to integrate InsideOut with their existing learning management systems', 1, 95.6812, 4.31884, NULL, '{\"text-davinci-002\": 1.7887072637677193}', 95.6812),
(960, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 2, 'We will also explore the possibility of offering individual plans for students who wish to verify their work before submitting it', 1, 50.8838, 49.1162, NULL, '{\"bloomz\": 5.97538985311985, \"mixtral-8x7b\": 2.6466546580195427, \"t0_11b\": 8.890213817358017, \"t0_3b\": 7.22789466381073, \"text-davinci-002\": 8.18437859416008}', 50.8838),
(961, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 4, 'Future Vision: Our vision is to make InsideOut the world\'s leading solution to combat plagiarism in educational institutions', 0, 38.3778, 61.6222, 'text-davinci-002', '{\"GLM130B\": 8.547049760818481, \"t0_11b\": 7.936743646860123, \"t0_3b\": 2.687281370162964, \"text-davinci-002\": 23.24804663658142, \"text-davinci-003\": 2.6593580842018127}', 61.6222),
(962, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 5, 'We aspire to be recognized as the gold standard in academic integrity, thereby helping to foster genuine inquiry and creativity in future generations of students', 0, 20.0697, 79.9303, 'gpt-3.5-turbo', '{\"gemma-7b-it\": 8.667504787445068, \"gpt-3.5-turbo\": 18.802092969417572, \"llama3-70b\": 6.971973925828934, \"llama3-8b\": 7.694951444864273, \"t0_11b\": 13.913755118846893}', 79.9303),
(963, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 6, 'In the future, we plan to expand our presence internationally and collaborate with educational and government organizations to promote academic integrity on a global scale', 0, 13.6667, 86.3333, 't0_11b', '{\"flan_t5_base\": 4.916928336024284, \"flan_t5_large\": 4.35618944466114, \"flan_t5_small\": 3.1140193343162537, \"t0_11b\": 43.71527135372162, \"t0_3b\": 25.554487109184265}', 86.3333),
(964, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 8, 'Future Innovations: In our commitment to continue to be a leader in the field of academic integrity, we are planning to implement the following innovations in the future: Multimodal Analysis: We will improve our platform so that it can analyze not only text and images, but also content in more complex formats, such as videos and presentations, thus extending plagiarism detection to new forms of academic presentation', 1, 62.2276, 37.7724, NULL, '{\"opt_2.7b\": 2.3746097460389137, \"opt_30b\": 2.2592948749661446, \"opt_6.7b\": 3.5849109292030334, \"opt_iml_30b\": 13.941952586174011, \"opt_iml_max_1.3b\": 9.568029642105103}', 62.2276),
(965, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 9, 'Paraphrase Identification: We will develop advanced techniques to detect paraphrases and rewriting of texts, which will allow us to identify more sophisticated and subtle cases of plagiarism', 0, 5.38276, 94.6172, 't0_11b', '{\"flan_t5_base\": 7.789625972509384, \"flan_t5_large\": 6.5559931099414825, \"flan_t5_small\": 6.732261925935745, \"t0_11b\": 39.389920234680176, \"t0_3b\": 24.289600551128387}', 94.6172),
(966, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 10, 'Integration with Conversational Artificial Intelligence: We will take advantage of the capabilities of conversational artificial intelligence to improve the user experience, allowing teachers to interact with the platform and obtain results faster', 0, 2.44282, 97.5572, 't0_11b', '{\"flan_t5_base\": 4.838467016816139, \"flan_t5_large\": 3.8294803351163864, \"flan_t5_small\": 5.2231717854738235, \"t0_11b\": 44.13602352142334, \"t0_3b\": 28.322163224220276}', 97.5572),
(967, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 11, 'Media Content Analysis: We will implement media analysis recognition technologies to detect plagiarism in recorded speech and live broadcast content, thus addressing new forms of unauthorized copying', 0, 16.1308, 83.8692, 't0_11b', '{\"flan_t5_base\": 9.361135959625244, \"flan_t5_large\": 8.757440000772476, \"flan_t5_small\": 7.2495609521865845, \"t0_11b\": 24.598436057567596, \"t0_3b\": 17.43338257074356}', 83.8692),
(968, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 12, 'Generative Adversarial Neural Networks (GANs): We will investigate the use of GANs to help students prevent plagiarism from the stage of creating academic papers', 0, 6.83418, 93.1658, 't0_11b', '{\"flan_t5_base\": 10.402149707078934, \"flan_t5_large\": 4.183986410498619, \"flan_t5_small\": 3.9208736270666122, \"t0_11b\": 37.08020746707916, \"t0_3b\": 28.949549794197083}', 93.1658),
(969, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 14, 'Conclusions: InsideOut is positioned as the most advanced and reliable anti-plagiarism platform on the market', 1, 79.5706, 20.4294, NULL, '{\"GLM130B\": 5.401511117815971, \"t0_11b\": 1.0953069664537907, \"text-davinci-002\": 5.5885422974824905, \"text-davinci-003\": 3.899930790066719}', 79.5706),
(970, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 15, 'Our focus on plagiarism detection in various types of content and backed by an exceptional customer experience set us apart from other solutions available', 1, 91.6106, 8.38936, NULL, '{\"GLM130B\": 1.2019029818475246, \"opt_13b\": 1.9402652978897095}', 91.6106),
(971, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 16, 'With InsideOut, educational institutions can guarantee the originality and authenticity of their students\' work, promoting an ethical and nurturing learning environment', 0, 35.3269, 64.6731, 'text-davinci-003', '{\"gemma-7b-it\": 8.96531268954277, \"gpt-3.5-turbo\": 16.73201322555542, \"llama3-8b\": 5.431849882006645, \"text-davinci-002\": 4.360377788543701, \"text-davinci-003\": 17.930275201797485}', 64.6731),
(972, 'b5e151b5-4802-4879-8eb6-f025146c8790', 2, 17, 'We look to the future with enthusiasm, committed to continuing to develop innovative technologies that protect academic integrity and foster creativity in the world of education', 0, 4.54033, 95.4597, 't0_11b', '{\"flan_t5_base\": 3.209869936108589, \"flan_t5_large\": 5.282826349139214, \"t0_11b\": 45.47316133975983, \"t0_3b\": 19.274170696735382, \"text-davinci-002\": 4.117796570062637}', 95.4597);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contact_interactions`
--

CREATE TABLE `contact_interactions` (
  `id` int(11) NOT NULL,
  `contact_id` varchar(36) NOT NULL,
  `user_id` int(11) NOT NULL,
  `interaction_type` varchar(50) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `outcome` varchar(100) DEFAULT NULL,
  `next_action` varchar(255) DEFAULT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `scheduled_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contact_sales`
--

CREATE TABLE `contact_sales` (
  `id` int(11) NOT NULL,
  `contact_id` varchar(36) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `company_name` varchar(200) DEFAULT NULL,
  `job_title` varchar(150) DEFAULT NULL,
  `company_size` varchar(50) DEFAULT NULL,
  `industry` varchar(100) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `service_interest` varchar(100) NOT NULL,
  `budget_range` varchar(50) DEFAULT NULL,
  `timeline` varchar(50) DEFAULT NULL,
  `message` text NOT NULL,
  `source` varchar(100) DEFAULT NULL,
  `utm_source` varchar(100) DEFAULT NULL,
  `utm_medium` varchar(100) DEFAULT NULL,
  `utm_campaign` varchar(100) DEFAULT NULL,
  `referrer_url` varchar(500) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'new',
  `priority` varchar(20) DEFAULT 'medium',
  `assigned_to` int(11) DEFAULT NULL,
  `lead_score` int(11) DEFAULT 0,
  `estimated_value` float DEFAULT NULL,
  `last_contact_date` datetime DEFAULT NULL,
  `next_followup_date` datetime DEFAULT NULL,
  `contact_attempts` int(11) DEFAULT 0,
  `internal_notes` text DEFAULT NULL,
  `tags` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`tags`)),
  `user_agent` varchar(500) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `contacted_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `container_status`
--

CREATE TABLE `container_status` (
  `id` int(11) NOT NULL,
  `container_id` varchar(255) NOT NULL,
  `container_name` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `running` tinyint(1) NOT NULL DEFAULT 0,
  `health` varchar(50) DEFAULT NULL,
  `cpu_usage` float DEFAULT NULL,
  `memory_usage` float DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Country`
--

CREATE TABLE `Country` (
  `id` int(11) NOT NULL,
  `country` varchar(100) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Country`
--

INSERT INTO `Country` (`id`, `country`, `user_id`, `created_date`) VALUES
(1, 'Dominican Republic', NULL, '2024-02-19 19:59:59'),
(2, 'Canada', NULL, '2024-02-19 19:59:59'),
(3, 'United States', NULL, '2024-02-19 19:59:59'),
(11, 'Francia', NULL, '2025-07-01 23:34:22');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Docmodels`
--

CREATE TABLE `Docmodels` (
  `id` int(11) NOT NULL,
  `institution_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `lenguage_id` int(11) DEFAULT NULL,
  `accuracy` varchar(50) DEFAULT NULL,
  `model` varchar(255) DEFAULT NULL,
  `vectorizer` varchar(255) DEFAULT NULL,
  `xtrain` varchar(255) DEFAULT NULL,
  `update_date` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Doctype`
--

CREATE TABLE `Doctype` (
  `id` int(11) NOT NULL,
  `doctype` varchar(4) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Doctype`
--

INSERT INTO `Doctype` (`id`, `doctype`, `user_id`, `created_date`) VALUES
(1, 'PDF', NULL, '2024-02-19 20:03:32'),
(2, 'DOC', NULL, '2024-02-19 20:03:32'),
(3, 'DOCX', NULL, '2024-02-19 20:03:32'),
(4, 'XPS', NULL, '2024-02-19 20:03:32'),
(5, 'EPUB', NULL, '2024-02-19 20:03:32'),
(6, 'MOBI', NULL, '2024-02-19 20:03:32'),
(7, 'FB2', NULL, '2024-02-19 20:03:32'),
(8, 'CBZ', NULL, '2024-02-19 20:03:32'),
(9, 'TXT', NULL, '2024-02-19 20:03:32');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Documents`
--

CREATE TABLE `Documents` (
  `id` int(11) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `author` varchar(255) DEFAULT NULL,
  `content` longtext DEFAULT NULL,
  `rena` varchar(255) DEFAULT NULL,
  `theme` varchar(55) DEFAULT NULL,
  `doctype_id` int(11) DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  `institution_id` int(11) DEFAULT NULL,
  `lenguage_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Documents`
--

INSERT INTO `Documents` (`id`, `title`, `author`, `content`, `rena`, `theme`, `doctype_id`, `country_id`, `institution_id`, `lenguage_id`, `user_id`, `created_date`) VALUES
(1, 'Untitled', '', 'The LinnSequencer 32 Track MIDI Sequence Recorder The LinnSequencer is a state-of-the-art composition and performance tool for the professional musician. It is extremely powerful, yet amazingly simple to learn and use. It’s many remarkable features include: ¢ Operation is similar to multi-track tape recorder with PLAY, STOP, RECORD, FAST FORWARD, REWIND, and LOCATE controls. e Each of the 100 sequences contains 32 simultaneous, polyphonic tracks. Each track may be assigned to one of 16 MIDI channels. Simultaneously plays up to 16 polyphonic synthesizers! ¢ Ultra-fast 3%” disk drive stores complex songs in seconds and holds over 110,000 notes per disk! ¢ One or all tracks may be TRANSPOSED at the touch of a key. e Exclusive real-time ERASE function makes editing FAST. * Exclusive REPEAT function automatically repeats any held notes at a pre-selected rhythmic value. ¢ TIMING CORRECTION works during playback and operates without ‘chopping’ notes. ¢ Optional SMPTE time code synchronization. © Optional remote control. Recording a Sequence To record a sequence, simply press RECORD and PLAY, then play your MIDI keyboard in time to the Sequencer’s click track. When the sequence loops back around to bar 1, you’ ll hear what you played—only all timing errors will be corrected! (Timing correction may be adjusted or defeated). Any additional notes played will be added into the track — existing notes are not erased while recording! FAST FORWARD, REWIND, and LOCATE controls may be used at any time to quickly access any location in your sequence for spot-recording. To overdub a new part, select a different track and start recording—while you record, the first track will play in perfect sync (unless you MUTE it, or SOLO another track). In this way, up to 32 tracks may be overdubbed! All MIDI effects are recorded including pitch bend, modulation, velocity, aftertouch, sustain pedal, and program changes! Editing To erase a wrong note, simply hold ERASE and press the note to be erased just before it plays in the sequence— when played back, it will be gone. Notes may also be added, erased, or changed using the SINGLE STEP func- tion. To overdub notes at specific points within a sequence, Additional Features simply use LOCATE, FAST FORWARD, or REWIND to find the desired bar number, then start recording. The INSERT/COPY function allows you to move bars from one location to another—in the same sequence or a different one. For example, you might insert a copy of the first verse between the second chorus and the bridge. DELETE BARS operates the same way to remove unwanted sections, Creating a Song One way to create a song is to record each track all the way through (up to 999 bars). Another way is to record each basic section (verse, chorus, etc.) in individual sequences, then use the CREATE SONG function to “chain” them together. CREATE SONG will then automatically copy all the parts into a new sequence. If desired, you can even set the last few bars to repeat infinitely, for a fadeout. Composition Without Compromise The technology you use should never be so complex that it interferes with the creative process. That’s precisely why the LinnSequencer is designed to let you compose, record and edit while devoting your undivided attention to your music. See your Linn dealer today for a demonstration! * Simple, easy to learn operation—the 32 character LCD display clearly guides you through all operations. If needed, the HELP button displays additional explanations. * Non-destructive recording—existing notes are not erased while recording. ¢ Two FOOTSWITCH INPUTS may be assigned to remotely control many of the commonly used functions, including ERASE, REPEAT, PLAY/STOP, or LOCATE. ¢ Iwo TRIGGER OUTPUTS may be programmed to output pulses at any selected note value. © Will sync to standard LinnDrum or Linn 9000 sync tone. © Utilizes ultra high-speed, 8 MHz 80186 16 bit computer internally for FAST operation. * TEMPO may be specified in BEATS-PER-MINUTE or FRAMES-PER-BEAT at 24, 25, or 30 frames per second, (even drop frame!) ¢ TEMPO may be entered numerically, adjustable in tenths of a Beat-Per-Minute increments, or by tapping quarter notes on the TAP TEMPO button. ¢ TEMPO CHANGES may be programmed into a sequence, with smooth transitions if desired. ¢ Any TIME SIGNATURE may be used, and may be changed within a song. linn Linn Electronics, Inc. 18720 Oxnard Street, Tarzana, CA 91356 (818) 708-8131 TELEX #298949 LINN URThe LinnSequencer 32 Track MIDI Sequence Recorder The LinnSequencer is a state-of-the-art composition and performance tool for the professional musician. It is extremely powerful, yet amazingly simple to learn and use. It’s many remarkable features include: ¢ Operation is similar to multi-track tape recorder with PLAY, STOP, RECORD, FAST FORWARD, REWIND, and LOCATE controls. e Each of the 100 sequences contains 32 simultaneous, polyphonic tracks. Each track may be assigned to one of 16 MIDI channels. Simultaneously plays up to 16 polyphonic synthesizers! ¢ Ultra-fast 3%” disk drive stores complex songs in seconds and holds over 110,000 notes per disk! ¢ One or all tracks may be TRANSPOSED at the touch of a key. e Exclusive real-time ERASE function makes editing FAST. * Exclusive REPEAT function automatically repeats any held notes at a pre-selected rhythmic value. ¢ TIMING CORRECTION works during playback and operates without ‘chopping’ notes. ¢ Optional SMPTE time code synchronization. © Optional remote control. Recording a Sequence To record a sequence, simply press RECORD and PLAY, then play your MIDI keyboard in time to the Sequencer’s click track. When the sequence loops back around to bar 1, you’ ll hear what you played—only all timing errors will be corrected! (Timing correction may be adjusted or defeated). Any additional notes played will be added into the track — existing notes are not erased while recording! FAST FORWARD, REWIND, and LOCATE controls may be used at any time to quickly access any location in your sequence for spot-recording. To overdub a new part, select a different track and start recording—while you record, the first track will play in perfect sync (unless you MUTE it, or SOLO another track). In this way, up to 32 tracks may be overdubbed! All MIDI effects are recorded including pitch bend, modulation, velocity, aftertouch, sustain pedal, and program changes! Editing To erase a wrong note, simply hold ERASE and press the note to be erased just before it plays in the sequence— when played back, it will be gone. Notes may also be added, erased, or changed using the SINGLE STEP func- tion. To overdub notes at specific points within a sequence, Additional Features simply use LOCATE, FAST FORWARD, or REWIND to find the desired bar number, then start recording. The INSERT/COPY function allows you to move bars from one location to another—in the same sequence or a different one. For example, you might insert a copy of the first verse between the second chorus and the bridge. DELETE BARS operates the same way to remove unwanted sections, Creating a Song One way to create a song is to record each track all the way through (up to 999 bars). Another way is to record each basic section (verse, chorus, etc.) in individual sequences, then use the CREATE SONG function to “chain” them together. CREATE SONG will then automatically copy all the parts into a new sequence. If desired, you can even set the last few bars to repeat infinitely, for a fadeout. Composition Without Compromise The technology you use should never be so complex that it interferes with the creative process. That’s precisely why the LinnSequencer is designed to let you compose, record and edit while devoting your undivided attention to your music. See your Linn dealer today for a demonstration! * Simple, easy to learn operation—the 32 character LCD display clearly guides you through all operations. If needed, the HELP button displays additional explanations. * Non-destructive recording—existing notes are not erased while recording. ¢ Two FOOTSWITCH INPUTS may be assigned to remotely control many of the commonly used functions, including ERASE, REPEAT, PLAY/STOP, or LOCATE. ¢ Iwo TRIGGER OUTPUTS may be programmed to output pulses at any selected note value. © Will sync to standard LinnDrum or Linn 9000 sync tone. ® Utilizes ultra high-speed, 8 MHz 80186 16 bit computer internally for FAST operation. * TEMPO may be specified in BEATS-PER-MINUTE or FRAMES-PER-BEAT at 24, 25, or 30 frames per second, (even drop frame!) ¢ TEMPO may be entered numerically, adjustable in tenths of a Beat-Per-Minute increments, or by tapping quarter notes on the TAP TEMPO button. ¢ TEMPO CHANGES may be programmed into a sequence, with smooth transitions if desired. ¢ Any TIME SIGNATURE may be used, and may be changed within a song. nn Linn Electronics, Inc. 18720 Oxnard Street, Tarzana, CA 91356 (818) 708-8131 TELEX #298949 LINN UR2A NNI‘I 6F6867# XATALL IE18-80L (818) 9SEI6 VO “BUBZIRY, “J0aNS PIPUXO OZLEI “Uy ‘soTUOMOI,q UUrT uut] “‘SUOS B UIJIM pasueyo oq ABU pue ‘posn oq AWW AYN IVNOIS AWLL AUV “parlsop Jr SUOTIISUBI} YIOOUIS YIM “BoueNbas eB OJUI pourtueIZOId 9q ABU SFONWHO OdINAL e ‘uonng OdNAL dV L 9) uO sojou Jayienb Suiddy} Aq 10 ‘syUSTIOIOUI oINUTIAI-J8g-Jesg & JO sys} UL ofquisn(pe ‘ATTeouIAUINU paiajus oq ABU OdINALL e (jouer doup u3a9) “puooes Jed souely O€ 10 “SZ “pz 18 [LVAG-MAd-SHN VU 10 ALOANIWAAd-SLVAd U! patyoeds aq kewl OAL « ‘uoTe1odo [SVx JO} Aj[eusoyUT JoyndUIOd 11g 9] 98108 ZHI 8g ‘poeds-ysry Bann soz] e \"9U0} DUAS 0006 UUL] Jo wNIqUUr] prepue}s 0} OUAS [ITAA © “ONYBA 9}OU poloapes Aue Je sas—nd jndyno 07 pewureigold 3q ACW SL Ad LNO YADONAL OML \"ALVOOT 10 GOLS/AV 1d ‘LWddad “ASV SUIpNpoUr ‘suOTIOUN] posn A[UOUILUOS 94] JO AUBUT [O1]UOD AJ9]OWIAI 0} PousIsse oq ACUI ST AdNI HOLIMSLOO OME « “SUIPIONAI I[IYM P2sesd JOU Iv $3}OU BUTISIXO—ZUIPIOIA SATON.ASOP-UON ‘suoneurldxa peuoyippe sdeydsip uowng g1TqH oy] ‘pepsau JI ‘suoneiodo [ye yYsnosy] NOA sapins ApIespo Avfdsip QO] Joey Z7¢ 9y3—uoeIodo Urea] 0} Ased ‘aus « jUorel]suowtap & IO} Aepol Jayeap uur’] INOA dag ‘dISHUL INOA 0} UONUS}]¥ PaplAIPUN INOA SUTJOASp ITY ps pue p1osai ‘asoduod no Jay 0} pausisap st 1s0uenbesuur’] oy) Aum Aposiooid $,Jeu], ‘SS9d0Id SATTBS1D OY} YIM SOIOJIOIUT yey) xo]dwWI0d Os dq JOA9U P[NoUsS osn NOA AZopOuYdE} oy ISTUMOIAUIO?) NOAA UOHISOdWIO) \"NOSpr] B Oy ‘AONUTJUT yada 0} seq Maz Se] BY] Jas UdAd uvd NOA ‘palisap JJ ‘souanbes Mou ¥B OVUT sjied ou] [Te Adoo ATesrewO Ne WI) [IM ONOS ALVAAO JeyIe80} wey} ,deyd,, 0} UOTOUNJ ONOS ALVA ou] asn usy] ‘saouanbes JENPIAIpUt UI (“949 ‘snJOYD ‘aS1OA) UOTIDIS JIseq Yes Pl0da1 OF ST ABM JOuIOUY “(812g 666 01 dn) ysnory) ABM dU} [fe YORI] YORs p10991 0} ST SUOS B 9789I9 0} ABM SUG, SUOS & SUTVAID *suoT}oes poJUBMUN SAOUIOI 0} ABM SWS dU} SoyeIodo SUV ALATAaG “OBPLIq dy} PUB SNIOY PUOdAS dT]] Ud9MIAQ SIDA ISI ay) Jo Adoo B JJasuT WYSE NOAA ‘afdwexs 10.f ‘UO JUSIN]JIP B IO aouaNbas sues OY} UI—JOY OUP 0} UOTIEIO] 9UO WOT] $1Bq JAOUI OF NOA sMOTIe WOTIOUNS AdOO/IMASNI OULL ‘SUIPIONAI JIVIS Udy) “OQuINU eq porisop ay} puy 0} CNIMAY 10 ‘CYVM Od LSWA “AEVOOT esn Apduns sainjeay [PUOHIPPY ‘gouanbas & UTYIIM s]UTOd a1y1dads 3¥ $9100 QnPIOAO OL \"UOT} -ouns dALLS ATONIS 24) Suisn pasueyo Jo ‘pasesa ‘pappe aq osye ABUT S9]ON ‘U0 9q ]IIM 1 “yoeq podeyd uayM —aouanbas oy] ul skeyd 71 a10J9q Isnf posers oq 0} d]0U ayy ssaid pue ASvwug ploy Aydunis ‘jou Suomm & aseso OL sunipa jsesdueyo ureisoid pue ‘fepod ureysns ‘yonoplalje ‘AWOOTOA ‘UOTyeTNpow ‘pusg youd Surpnyour pep10del are $199JJ2 TCTIN [WV iPeqqnpseao aq Aeur syoen Ze 07 dn ‘Kem sie Uy *(foeI} JOyOUR OJOS 10 ALLAN NOA ssofum) duAS yOaysod ul Avy [[IM Yow] ISI 93 “prooar NOA 3[IYM—SUIPIOIA LIBIS PU YORI) TUdIOTJIP B JOaTas *y1ed MOU B QNPIsA0 OL, “SuIps0daJ-jods 10} aouanbes mno0k UI UOHBIO] Aue ssad0e ATYOIND 0} owt} Aue ye pasn aq AvUE SJONUOD FLIVOOT pur ‘ANIMA ‘CYVMaYOd LSVd {SUIPIOSAI {IY posesa JOU se So]OU SuTsTXO— yous} 3U} OUT poppe aq JIM poteyd sajou yeuonippe Auy *(povesjap 10 poysn{pe oq ABW UOTIIII0D BUTUTT]) j{paqoeLI09 2q ][IM S1OLIe Sur [fe ATUO—patey]d nod Jey Jedy ]],NOA ‘] req 0] punose yoeq sdoo] sduanbas ay] Udy AA “YOu Yor §,sa0uaNbas at} O] SUIT) UI preogday [IW] INO Avy usy3 AV\'1d pue (YOON ssoid Ayduus ‘aousnbes & p1o09es OF, g0uaNbas & SUIP10I0y] ‘JONWOD s}JouNaI TeuONdGO e \"UOTJEZIUOIYUAS OPOS UIT} FLAWS [euondo e ‘sou .sulddoys, noyyM sayelodo pue yoegdvyd ZuLINp S¥IOM NOLLOANNYOO ONIWILL e ‘onqea ory AY pojoojes-oid & ye sajou pyoy Aue syeadas ATTeONewWO Ne UOTOUNS [WAdAY OAISNOX e ‘LSVJ SUnIpS soyeu UOTOUN ASV UA OUlN-[eal SAISNIOXY e ‘Koy B JO YONO} 941 12 CASOdSNVALL 0g ABU Syde] [Te 10 9UC e i ASIP Jed S9}0U OOO‘OTT JOA SpfOy puv SpUOdeS UT SBUOS Xa[AUIOD So10}S DALIP YSIP , 74 € ISCJ-CNIN jSIOZISOUJUAS stuoydAjod of 0} dn skeyd A[snoourynuls ‘spouueYd [IW 9T JO duo 0} pousisse oq ABUL YORI] YOR ‘syous) oruoydAjod ‘snoouelnurs 7¢ SuTeJUOS ssouUaNbas QO] OY} JO YORA e ‘SJONUOS ATWOOT pur ‘GNIMAY ‘GaVM OA LSVd ‘GYOOde AOLS ‘AV Td YIM Jopsocas ade} Yowsj-N[NU O} eps st UOTLISdO @ LOPNOUT SaINjeoy s[quyIeUlss AUB S.JJ ‘OSN pue UIes] 0} o[duns A[suIzeUe JOA ‘PnJsomod APOUIOITXO St 1] “UeIOIsNUL feUOIssajoid oY} 10 JOO} soUBULIOJIJAd pue UOTIsOduIOS 11e-dY1-JO-9}e)s B SI IONUANbDaguUT] ay JOps1odady soUINbIS [GTI YVAL ZE Jgouanbaguury oy2A NNI‘I 6F6867# XATALL IE18-80L (818) 9SEI6 VO “BUBZIRY, “J0aNS PIPUXO OZLEI “Uy ‘soTUOMOI,q UUrT uu “‘SUOS B UIJIM pasueyo oq ABU pue ‘posn oq AWW AYN IVNOIS AWLL AUV “parlsop Jr SUOTIISUBI} YIOOUIS YIM “BoueNbas eB OJUI pourtueIZOId 9q ABU SFONWHO OdINAL e ‘uonng OdNAL dV L 9) uO sojou Jayienb Suiddy} Aq 10 ‘syUSTIOIOUI oINUTIAI-J8g-Jesg & JO sys} UL ofquisn(pe ‘ATTeouIAUINU paiajus oq ABU OdINALL e (jouer doup u3a9) “puooes Jed souely O€ 10 “SZ “pz 18 [LVAG-MAd-SHN VU 10 ALOANIWAAd-SLVAd U! patyoeds aq kewl OAL « ‘uoTe1odo [SVx JO} Aj[eusoyUT JoyndUIOd 11g 9] 98108 ZHI 8g ‘poeds-ysry Bann soz] e \"9U0} DUAS 0006 UUL] Jo wNIqUUr] prepue}s 0} OUAS [ITAA © “ONYBA 9}OU poloapes Aue Je sas—nd jndyno 07 pewureigold 3q ACW SL Ad LNO YADONAL OML \"ALVOOT 10 GOLS/AV 1d ‘LWddad “ASV SUIpNpoUr ‘suOTIOUN] posn A[UOUILUOS 94] JO AUBUT [O1]UOD AJ9]OWIAI 0} PousIsse oq ACUI ST AdNI HOLIMSLOO OME « “SUIPIONAI I[IYM P2sesd JOU Iv $3}OU BUTISIXO—ZUIPIOIA SATON.ASOP-UON ‘suoneurldxa peuoyippe sdeydsip uowng g1TqH oy] ‘pepsau JI ‘suoneiodo [ye yYsnosy] NOA sapins ApIespo Avfdsip QO] Joey Z7¢ 9y3—uoeIodo Urea] 0} Ased ‘aus « jUorel]suowtap & IO} Aepol Jayeap uur’] INOA dag ‘dISHUL INOA 0} UONUS}]¥ PaplAIPUN INOA SUTJOASp ITY ps pue p1osai ‘asoduod no Jay 0} pausisap st 1s0uenbesuur’] oy) Aum Aposiooid $,Jeu], ‘SS9d0Id SATTBS1D OY} YIM SOIOJIOIUT yey) xo]dwWI0d Os dq JOA9U P[NoUsS osn NOA AZopOuYdE} oy ISTUMOIAUIO?) NOAA UOHISOdWIO) \"NOSpr] B Oy ‘AONUTJUT yada 0} seq Maz Se] BY] Jas UdAd uvd NOA ‘palisap JJ ‘souanbes Mou ¥B OVUT sjied ou] [Te Adoo ATesrewO Ne WI) [IM ONOS ALVAAO JeyIe80} wey} ,deyd,, 0} UOTOUNJ ONOS ALVA ou] asn usy] ‘saouanbes JENPIAIpUt UI (“949 ‘snJOYD ‘aS1OA) UOTIDIS JIseq Yes Pl0da1 OF ST ABM JOuIOUY “(812g 666 01 dn) ysnory) ABM dU} [fe YORI] YORs p10991 0} ST SUOS B 9789I9 0} ABM SUG, SUOS & SUTVAID *suoT}oes poJUBMUN SAOUIOI 0} ABM SWS dU} SoyeIodo SUV ALATAaG “OBPLIq dy} PUB SNIOY PUOdAS dT]] Ud9MIAQ SIDA ISI ay) Jo Adoo B JJasuT WYSE NOAA ‘afdwexs 10.f ‘UO JUSIN]JIP B IO aouaNbas sues OY} UI—JOY OUP 0} UOTIEIO] 9UO WOT] $1Bq JAOUI OF NOA sMOTIe WOTIOUNS AdOO/IMASNI OULL ‘SUIPIONAI JIVIS Udy) “OQuINU eq porisop ay} puy 0} CNIMAY 10 ‘CYVM Od LSWA “AEVOOT esn Apduns sainjeay [PUOHIPPY ‘gouanbas & UTYIIM s]UTOd a1y1dads 3¥ $9100 QnPIOAO OL \"UOT} -ouns dALLS ATONIS 24) Suisn pasueyo Jo ‘pasesa ‘pappe aq osye ABUT S9]ON ‘U0 9q ]IIM 1 “yoeq podeyd uayM —aouanbas oy] ul skeyd 71 a10J9q Isnf posers oq 0} d]0U ayy ssaid pue ASvwug ploy Aydunis ‘jou Suomm & aseso OL sunipa jsesdueyo ureisoid pue ‘fepod ureysns ‘yonoplalje ‘AWOOTOA ‘UOTyeTNpow ‘pusg youd Surpnyour pep10del are $199JJ2 TCTIN [WV iPeqqnpseao aq Aeur syoen Ze 07 dn ‘Kem sie Uy *(foeI} JOyOUR OJOS 10 ALLAN NOA ssofum) duAS yOaysod ul Avy [[IM Yow] ISI 93 “prooar NOA 3[IYM—SUIPIOIA LIBIS PU YORI) TUdIOTJIP B JOaTas *y1ed MOU B QNPIsA0 OL, “SuIps0daJ-jods 10} aouanbes mno0k UI UOHBIO] Aue ssad0e ATYOIND 0} owt} Aue ye pasn aq AvUE SJONUOD FLIVOOT pur ‘ANIMA ‘CYVMaYOd LSVd {SUIPIOSAI {IY posesa JOU se So]OU SuTsTXO— yous} 3U} OUT poppe aq JIM poteyd sajou yeuonippe Auy *(povesjap 10 poysn{pe oq ABW UOTIIII0D BUTUTT]) j{paqoeLI09 2q ][IM S1OLIe Sur [fe ATUO—patey]d nod Jey Jedy ]],NOA ‘] req 0] punose yoeq sdoo] sduanbas ay] Udy AA “YOu Yor §,sa0uaNbas at} O] SUIT) UI preogday [IW] INO Avy usy3 AV\'1d pue (YOON ssoid Ayduus ‘aousnbes & p1o09es OF, g0uaNbas & SUIP10I0y] ‘JONWOD s}JouNaI TeuONdGO e \"UOTJEZIUOIYUAS OPOS UIT} FLAWS [euondo e ‘sou .sulddoys, noyyM sayelodo pue yoegdvyd ZuLINp S¥IOM NOLLOANNYOO ONIWILL e ‘onqea ory AY pojoojes-oid & ye sajou pyoy Aue syeadas ATTeONewWO Ne UOTOUNS [WAdAY OAISNOX e ‘LSVJ SUnIpS soyeu UOTOUN ASV UA OUlN-[eal SAISNIOXY e ‘Koy B JO YONO} 941 12 CASOdSNVALL 0g ABU Syde] [Te 10 9UC e i ASIP Jed S9}0U OOO‘OTT JOA SpfOy puv SpUOdeS UT SBUOS Xa[AUIOD So10}S DALIP YSIP , 74 € ISCJ-CNIN jSIOZISOUJUAS stuoydAjod of 0} dn skeyd A[snoourynuls ‘spouueYd [IW 9T JO duo 0} pousisse oq ABUL YORI] YOR ‘syous) oruoydAjod ‘snoouelnurs 7¢ SuTeJUOS ssouUaNbas QO] OY} JO YORA e ‘SJONUOS ATWOOT pur ‘GNIMAY ‘GaVM OA LSVd ‘GYOOde AOLS ‘AV Td YIM Jopsocas ade} Yowsj-N[NU O} eps st UOTLISdO @ LOPNOUT SaINjeoy s[quyIeUlss AUB S.JJ ‘OSN pue UIes] 0} o[duns A[suIzeUe JOA ‘PnJsomod APOUIOITXO St 1] “UeIOIsNUL feUOIssajoid oY} 10 JOO} soUBULIOJIJAd pue UOTIsOduIOS 11e-dY1-JO-9}e)s B SI IONUANbDaguUT] ay JOps1odady soUINbIS [GTI YVAL ZE Jgouanbaguury oy', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/cardinal_2024-04-05-20-15-01/cardinal_2024-04-05-20-15-01.pdf', '', 1, 1, 1, 1, 2, '2024-04-06 08:15:13');
INSERT INTO `Documents` (`id`, `title`, `author`, `content`, `rena`, `theme`, `doctype_id`, `country_id`, `institution_id`, `lenguage_id`, `user_id`, `created_date`) VALUES
(2, 'gatekeeper logo', '', 'gatekeeperThe role of localorganisations insustainabledevelopment137b: August 2008The Evolution ofCasa Pueblo,Puerto Rico From Mining Oppositionto Community RevolutionAlexis Massol-González,Avril Andromache Johnnidis and Arturo Massol-DeyáThe roles of local organisations in poverty reduction and environmental managementAll poverty reduction is local. This is easy to forget given how discussion and debate onthe subject is dominated by bilateral aid agencies, development banks, national govern-ments and international NGOs. But regardless of higher level commitments anddecisions, what actually happens on the ground in particular localities is what makes thedifference. Many barriers to poverty reduction are local — local power structures, landowning patterns and anti-poor politicians, bureaucracies and regulations. Much of whatthe poor require — schools, healthcare, water and sanitation, land, social safety nets,getting onto voter registers — must be obtained from local organisations within thislocal context.Local organisations have a major role in addressing these realities, helping poor groupsaccess entitlements and engage with government. They may be local NGOs, grassrootsorganisations of the poor, or even local governments or branches of higher levels ofgovernment. But they function on a local level, have intimate knowledge of the localcontext and should be accountable to local people. Many operate on very small budgets,outside the main funding flows and frameworks. Yet they are not isolated from largergovernance issues; indeed, much pro-poor political change has been catalysed by localinnovations and by political pressure from grassroots organisations and their associations.This publication is one in a series of case studies and synthesis papers looking at thework of local organisations in development and environmental management. Thesepublications were developed in collaboration with the local organisations they profile.They seek to encourage international funding agencies to rethink the means by whichthey can support, work with and learn from the local organisations that are such acritical part of pro-poor development.IIED and its partners are grateful to Irish Aid,The Dutch Ministry of Foreign Affairs (DGIS),The Department for International Development (DFID), and The Norwegian Agency forDevelopment Cooperation (NORAD) for their support for this work on local organisations.The gatekeeper series of the Natural Resources Group at IIED is produced by theSustainable Agriculture, Biodiversity and Livelihoods Programme. The series aims tohighlight key topics in the field of sustainable natural resource management. Each paperreviews a selected issue of contemporary importance and draws preliminary conclusions fordevelopment that are particularly relevant for policymakers, researchers and planners.References are provided to important sources and background material. The series ispublished three times a year and is supported by the Swedish International DevelopmentCooperation Agency (Sida) and the Swiss Agency for Development and Cooperation(SDC). The views expressed in this paper are those of the author(s), and do not necessarilyrepresent those of the International Institute for Environment and Development (IIED), theSwedish International Development Cooperation Agency (Sida), the Swiss Agency forDevelopment and Cooperation (SDC) or any of their partners.Alexis Massol-González is a civil engineer by training and the founder and Director ofCasa Pueblo of Adjuntas. Avril A. Johnnidis is a junior at Harvard University majoring inbiological anthropology and political science; she has completed an internship with CasaPueblo. Arturo Massol-Deyá is a professor of microbiology at the University of PuertoRico at Mayagüez and President of Casa Pueblo Trust. Contact details: Apartado 704,Adjuntas, Puerto Rico 00601; Telephone/Fax + 1 787 829 4842; Email: casapueb@coqui.netThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution1Executive summaryCasa Pueblo began as a grassroots’ citizens group formed to oppose the Puerto Ricangovernment’s plan to allow large-scale open-pit mining by international corporations in thecentral region in 1980. Its aims have since evolved to promoting community self-reliance andcommunity-based self-management, while conserving cultural heritage and local andnational ecological integrity. Its philosophy is based on a “social transformation model”: theaffirmation of cultural (local) values, reinforcement of self-esteem, and promotion of self-reliance and self-responsibility. It implements this through community culture (i.e. throughthe use of art, music and field action), information gathering, sound science and research,and self-sufficiency through community enterprises, such as coffee production, a communitystore and eco-tourism. In addition to successfully preventing the planned mining project, Casa Pueblo has alsochanged national mining and forestry policy. It has promoted sustainable forestry, developinga string of pro-poor, pro-environment forest reserves; developed a model of community-based forest management; influenced government to create a national forest fund for thepurchase and conservation of land of high ecological value; created the nation’s first biolog-ical corridor; shaped landscapes through encouraging better farming practices; launched anenvironmental education programme; brought scientific advice into the organisation; anddemonstrated options for the use of renewable energy. Casa Pueblo has faced many difficulties, including opposition from vested interests in mining,and government opposition or indifference. This was addressed through diversification,building the support of stakeholders and supporters, and gaining people’s trust throughopenness, transparency, and including the community in the decision-making process. CasaPueblo has developed ties at the local and national levels with relevant ministries, localdonors and the media. Puerto Rico’s international isolation due to its colonial political statusinitially meant limited access to external funding, international fora, and global communitynetworks, although its networking efforts and increasingly high profile have begun to improvethis situation. The organisation’s future plans focus on strengthening and protecting itsachievements: improving the management structure to facilitate inter-generational changes;and encouraging horizontal growth through the social transformation of both local andmore distant communities. It is also seeking alternative forms of financing that could enablescaling-up.2gatekeeper 137b: August 2008The Evolution of Casa Pueblo,Puerto RicoFrom Mining Opposition to Community Revolution Alexis Massol-González, Avril Andromache Johnnidis andArturo Massol-DeyáCasa Pueblo’s evolutionSaying “no” to mines: the catalyst for Casa PuebloIn 1980, the government of Puerto Rico announced its intention to allow large-scaleopen pit mining by multinational corporations in the centre of the island. In thepreceding decades the region had been included in the central government’s territorialplans as a “mining area”.This designation prompted the eviction of residents in order toexpand mining. Abandonment of agricultural activities, the closure of the local sugarmill, a decline in coffee farming, the closure of schools, and the denial of constructionlicenses for churches and houses had all led to severe social marginalisation and remark-able levels of unemployment.These events allowed multinational corporations based inthe United States to purchase lands at low cost, especially where the richest deposits ofgold, silver, and copper were located. Faced with the prospect that the governmentwould now issue mining permits that would result in ecological disaster, widespreadpollution of all kinds, and compromise the social, cultural, and economic integrity of thenearby communities, a grassroots citizens’ group organised themselves into the Taller deArte y Cultura (Art and Culture Workshop) in Adjuntas, a small town in the island’scentral mountain region. The group, now known as Casa Pueblo, began with three basictasks to launch a process of community organising and self-determination:1. gathering scientific knowledge2. developing a policy3. strategy planningScientific knowledge: the key to the campaign In order to learn more about the government and mining company’s specific plans, thegroup gathered official documents and scientific studies.They found that 17 mineral bedssuitable for commercial exploitation had been identified around Adjuntas and thesurrounding municipalities.The proposal for mining would include nearly 14,000 hectaresThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution3(ha) of land in the central area of the island and the extraction method would involvedigging massive craters up to almost 600 metres deep and almost 1,600 metres wide.Themining company’s own reports foresaw radical reductions in the flow of crucial watersources for 1 million people, contamination of air, agricultural soils, and sources of potablewater, as well as further problems of erosion, acid run-off, and sedimentation of lakes andrivers.Initially, the Taller de Arte y Cultura’s campaign was one of education, enlisting the help ofoutside experts to give lectures in the local communities.This focus on improving knowledgeabout the local situation strengthened the community-based process and the group decidedthat it must not be dependent upon the government, politicians, or even experts or advisersto decide the community’s fate, no matter what good intentions such actors may have. Suchdependence is neither healthy for the environment, nor for the community.Public policy from the bottom up Armed with the necessary knowledge, the group formed its own interpretation of thesocial, scientific, environmental, and political implications of the mining. It concluded thatthe main issue was neither who would exploit the mining deposits (whether Puerto Ricansor foreigners), nor who would obtain the profits (whether capitalists or workers)—thequestions with which earlier anti-mining opponents had concerned themselves.The mainissue was the indisputable threat to the integrity of the land and the health, culture andway of life of the people; in short, a threat to the survival itself of Puerto Rico as a nation.The situation was one of blatant colonialism, where foreign multinational corporationswould plunder the land, reap enormous profits, cripple traditional social structures andthe regional economy, and leave destruction in local communities. After assessing theproblem and viewing it through the lens of Puerto Rico’s colonial political status, the Tallerdeclared its own position: “No to mines under any condition”.Strategy planning for success With the problems identified and the Taller’s position towards them clear, the groupsought to devise a clear, efficient and meaningful campaign that would gather togetherdifferent sectors of the community with the intention, the will and the capacity toprevent mining activities. Initially, apathy, indifference and fear—due to repression andintimidation by the government—prevailed in the community. Furthermore, mostpeople actually favoured mining, including the municipal governments that organiseddemonstrations in the capital city to insist that Puerto Rican \"central development\",based on exploitation of non-renewable natural resources, should begin. However, thesefactions were generally not aware of the details or consequences of the mining proposal.Their intentions were either to economically support a potential Republic of Puerto Ricoor to sell the Puerto Rican statehood to the USA.Culture as an instrument for changeFaced with the imminent start of mining activities, a lack of people to actively partici-pate in the opposition movement, and organisational limitations, the small group of4gatekeeper 137b: August 2008committed citizens co-ordinated a series of educational lectures in various parts ofAdjuntas. The final event was to be a demonstration in the public square of the town,representing the first days of struggle against mining. However, apart from the organ-isers and their immediate family, virtually the only other people who attended thedemonstration were the police. This failure prompted a lengthy and deep process ofanalysis: what was the best way to garner public support and spark interest by thecitizens of Adjuntas in their own fate? The result was a realisation that local culture wasthe unifying agent. The group organised a number of cultural interest groups: acommittee of artisans, musicians, minstrels, a children\'s folk dance group, sceneshifters,and other collaborators. In this way, the initial small group of engaged citizens diversi-fied and multiplied.Based on this, the Taller prepared the Concierto Patria Adentro (Inner Homeland Concert),performing traditional Puerto Rican music in neighbourhoods, towns, schools, anduniversities under the slogan,“Sí a la Vida,No a las Minas” (“Yes to Life, No to Mines”).Themessage was no longer elitist, but became understandable and friendly. At the sametime, an extended campaign began that included press conferences, demonstrations,chiringas (kite) festivals, bulletins, murals, tree plantings and the gathering of thousandsof signatures. Through cultural and community activities, awareness of the miningsituation grew and the citizens of Adjuntas steadily became more and more determinedand committed to preventing ecological, economic, and social disaster, even in the faceof continued government repression and intimidation.After six more years of struggle and continuous activities, the group recorded a partialvictory when the government stated that it would abandon mining plans. One keyreason for this about-turn, admitted by the government and mining companies, was theopposition generated by the Taller de Arte y Cultura—Casa Pueblo. However, landscontinued to be classified for mining purposes; clearly the mining option had beendeflated but not yet defeated.Building Casa Pueblo’s infrastructure: a community effortAs the struggle continued to defend natural resources and for self-determination, aproject started that transcended negation and destruction, and instead affirmed thevalues that reinforce self-esteem. In 1985, the Taller de Arte y Cultura purchased andrenovated a large old house and transformed it into a new home for Puerto Ricanculture—Casa Pueblo. Casa Pueblo houses a room for exhibitions and cultural activities,a library, a shop selling local handcrafts, administrative offices and accommodation forexternal collaborators so they can stay and contribute to projects. Casa Pueblo operateson solar energy, possesses a weather station in one of its forests, as well as a hydroponicsgarden and a butterfly garden with nectar and host plants where the complete life cycleof Lepidoptera can be appreciated.Towards financial self-sufficiency Through the process of establishing a viable organisation, it became evident to thevolunteers at Casa Pueblo that economy is a fundamental aspect in shaping socialThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution5action, allowing for self-sufficiency and thus independence and self-determination.Withthis awareness of the link between economy and freedom, three initiatives to ensureCasa Pueblo’s economic self-sufficiency were born:•Café Madre Isla (Madre Isla Coffee)•The community store•The Madre Isla Farm Ecotourism Project Café Madre Isla promotes a culture of community collaboration and a commitment tosocial change. It depends on volunteer labour for processing, packaging and distributingcoffee from mountain farms. It has created many jobs, and attracts hundreds of peopleeach week to Casa Pueblo and the surrounding area’s restaurants and shops. It hasgenerated capital that enables the organisation to develop its infrastructure, fund newinitiatives, and support environmental research.The community store has grown steadily.The shop creates several direct and indirect jobs,and artists and local producers of natural soaps, handicrafts and other items benefit froma permanent market. A fare and equitable trade has been achieved between suppliers,the organisation and the ultimate beneficiaries. This is not just a regular store; it is aplace to foster extended educational and organisational processes in which thecustomers engage in Casa Pueblo’s work. Additionally, ordinary residents of Adjuntasbenefit from the thousands of visitors that Casa Pueblo receives each year and whopatronise local businesses like these.The Madre Isla Farm Ecotourism Project combines agriculture with tourism, ecology witheconomy, and community labour with solidarity. Madre Isla Farm includes rusticcottages to accommodate national and international visitors. Furthermore, the facilitiesact as logistical support for other community activities, including residential universitycourses, summer camps for students of public schools in other areas, and a residence forexchange programmes, such as the service learning programme Casa Pueblo maintainswith Michigan State University. Fees for using the facilities vary, depending on thefinancial solvency of users. Often they are free of charge for students, workers andpeople who approach Casa Pueblo wanting to support its community-based projects.This pricing flexibility enables the organisation to observe certain ethics of social justicewhile achieving the target operations of the ecotourism enterprise.A new chapter in the mining conflictIn 1992, the same government in Puerto Rico that had dismissed mining plans in 1986signed a new mining agreement with Southern Gold Resources.This time, with its accu-mulated experience of community-based management, Casa Pueblo took swift andadept action to change the government’s policy towards open pit mining, once and forall. The group decided on a strategy that would include the active and visible participa-tion of student, religious, civic, cultural and environmental sectors. This strong effort atthe local level was reinforced with a national publicity campaign involving the press,radio and television. The community organised the Foro del Pueblo (People\'s Forum), apublic hearing with an invitation to the Secretary of the Department of Natural and6gatekeeper 137b: August 2008Environmental Resources (DNER). After the Secretary presented the government’sposition on mining, a panel of local people including an engineer, farmer, doctor, teacher,priest and 15 children asked questions and pointed out the weaknesses of the DNER’splan. Casa Pueblo’s approach demonstrates the importance of transforming public forafrom passive lecture audiences into true dialogues.The community held many other events, such as cultural fiestas, concerts, and confer-ences at schools and universities.Also of real impact was a series of interviews publishedby the local press, presenting the opinions of Casa Pueblo and of the government.To topit all, a press conference called desde el cielo (from the sky) was held, during which anational television station broadcast the image of more than 800 students “writing”“Noto Mines” with their bodies in their high school car park.These few words underlined thegrowing participation of the community and their unequivocal opposition to thedestruction of their environment.Community processes require imagination, creativity and organisation, as well as ameans of expression that avoids self-righteousness and is open to debate, criticism andself-reflection.And above all, they require solidarity. In 1995, hundreds of people took tothe streets of Adjuntas and marched to the top of the most important local mineraldeposit to plant trees and so begin the restoration of the land from mining explorationactivities. Their intention was firm and their message was clear: “We have alreadydecided, No to Mines”. Days later, the government reversed its long-standing policy andpassed Law no. 1171, prohibiting open-pit mining anywhere in Puerto Rico. It was thesolid stance, the grassroots struggle, and the unwavering shared position of ordinarypeople that were ultimately able to change national public policy.From mines to forest In 1995, after defeating the “economic development” model based on destructivemining, Casa Pueblo began a campaign to designate the former mining area as a forestreserve. This involved drafting a proposal whose scientific and social content was validand understandable to ordinary people.The organisation’s justification for designating aforest reserve lay in the value of the lands themselves, their location between otherforest units (thus creating a biological corridor), and their importance in protecting theheadwaters of water basins.Even more difficult than drafting a proposal proved to be designing a strategy toimplement it. It was evident that many of the people who participated in the anti-miningcampaign did not feel the same motivation for forestry and their participation was limited.The tradition of the protest struggle against negative forces had become well rooted, butthe culture of proposing positive action needed more practice, understanding and develop-ment. It is one thing to oppose a destructive project; it is another to create from scratchan alternative positive project.As Nelson Mandela has said,“to be free is not merely to castoff one’s chains but to live in a way that respects and enhances the lives of others.”In spite of many setbacks, the process developed slowly but surely, while the boldness ofaction, strength of argument, and prestige of Casa Pueblo came together. A year later,and after an intense public fight and continued discussions with the DNER, the govern-The Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution7ment came to favour Casa Pueblo’s proposal to transform the former mining-designatedarea into a legally-protected nature reserve. Finally, and through community initiative,the long process concluded, prohibiting mining and turning the “project of destruction”into the new forest unit Bosque del Pueblo (People\'s Forest).Bosque del Pueblo and community-based managementThe great Puerto Rican philosopher and freedom-fighter María de Hostos once proposedthe need for establishing in the conscience not only the notion of claiming rights, butalso of putting into practice \"...the knowledge of rights and recognition of responsibili-ties.\" Committed to this principle, Casa Pueblo worked to strengthen individual initiativeas well as social co-operation when developing a community-based management modelfor Bosque del Pueblo.This community-based management model is based on individual initiative, collectivemanagement and participatory democracy. It requires participation and collaborationamong the local community, the forest’s closest neighbours, and local and nationaladministrations. This reintegration of the people with the forest has proven essential toextend conservation efforts beyond the currently protected areas. Furthermore, the co-operation of groups and organisations that contribute according to their capacities isnecessary.The process requires the administrative structure to be adaptive and to enablethe development of leadership, growth and learning of both organisers and participants.In Casa Pueblo’s case, the core group heavily depends on the diverse expertise of volun-teers. Experimentation is encouraged, allowing for much change and growth as well asknowledge gained from trial and error.Casa Pueblo uses a decision-making process that does not unduly hamper the organisa-tion’s objectives with bureaucracy such as rigid voting procedures.The primary means ofgovernance are dialogue and the inclusion of all individuals interested and involved in aparticular initiative.To achieve these goals, it is essential to maintain self-discipline and to cultivate devotionto voluntary duties.This is not an easy task, especially in a country where dependence isencouraged in so many aspects of life. This model is not the only and ultimate solutionfor resource management. Both its limitations and its greatness lie in the fact that it iscommunity-based. People make it work through their voluntary participation—andtherefore its outcomes are determined by the extent and limits of their contributions.Tomaximise the value of such an approach requires commitment, and prompt, efficientsupport. The goal is a broad management that involves communities intimately in theadministration of their natural heritage, as a reaction to privatisation and globalisation.Casa Pueblo’s model of community-based management began six months after theforest was formally designated as a natural reserve. The first step was to create acommunity-based Management Board to supervise the management plan, which dividedthe reserve into three areas: (i) natural area for visitors; (ii) restricted natural environ-ment area; and (iii) special protection area. The plan covers water, wildlife, vegetation,social and community environment, leisure, interpretation and education, forest facili-ties, research, cultural resources and landscape. Casa Pueblo built cabins for visitors,8gatekeeper 137b: August 2008compost toilets, interpretative paths, a playground for children, an open-air amphithe-atre and picnic areas. In addition, the group began to carry out biological inventories, andestablished a permanent plot for monitoring biodiversity. This enabled them to assessthe ecological succession in the forest and implement resource recovery practices toenrich the secondary forest with species of native trees, reforest sensitive areas, andcontrol soil erosion. Finally, Casa Pueblo believed that ecological recovery encompassesthe recovery of cultural heritage.The group re-established an indigenous ceremonial parkfrom the pre-Columbian era that had been uprooted for mining exploration.From a forest to ecosystem managementCasa Pueblo’s management of the Bosque del Pueblo encouraged them to rethink issuesof public policy for the conservation of natural resources at a national level.ThroughoutPuerto Rico, they saw unharmonious scattered “development”, which lacked organisa-tion or long-term financial vision, and which ignored the sustainability of the area’snatural resources. As it is, water resources are already scarce in poor communities,aquifers are increasingly degraded, and there is widespread pollution of soil, unprotectedwater basins and fragmentation of forests. Such problems compromise Puerto Rico’sfuture development, reducing the potential for self-sufficiency in a country already verydependent on external economies. Therefore, Casa Pueblo decided to add conservationstrategies to the national agenda so as to increase the number and extent of protectedareas. Before the designation of Bosque del Pueblo, Puerto Rico possessed only 4% ofprotected forest—far less than other Caribbean islands such as Martinique (70%),Guadalupe (36%), Jamaica (22%), Dominican Republic (19%) and Cuba (12%).To achieve this, Casa Pueblo began a community campaign nourished by funds fromMadre Isla Coffee, donations by friends of the environment and from the Cooperativa deAhorro y Créditos de Arecibo. Altogether the campaign raised more than US $100,000 topurchase 50.5 ha of forest of high ecological value. This forest protects the headwatersof the most important river in the country, supplying water to more than 25% of thepopulation. Casa Pueblo was thus able to establish its own forest reserve, as a first steptowards protecting a much larger area, the Bosque La Olimpia (the Olimpia forest).In addition to purchasing its own land, Casa Pueblo and supporters from various sectorsof Puerto Rico submitted a further proposal to the government, to create the Fondo deAdquisición y Conservación de Terrenos de Alto Valor Ecológico (Fund for the Purchase andConservation of High Ecological Value Lands). The goal of this community strategy is todouble the percentage of protected areas in Puerto Rico over the next 10 years. Thegovernment enacted this in 2003 as Law no. 268. The fund had an initial budget ofUS$20 million with subsequent allotments of around $5 million for the protection ofsensitive areas. These funds were used to buy a further 364 ha of forest adjacent to the50 ha already purchased, in order to establish the Bosque La Olimpia. This larger area offorest is also community-managed via Casa Pueblo. The fund has also enabled thegovernment to incorporate new areas into the existing state forests.Recognising the growing population density in the headwaters of many of the country’smain rivers, as well as the excessive fragmentation of forests for urban, industrial andThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution9agricultural activity, Casa Pueblo proposed and developed an even bigger initiative—anew landscape conservation plan. The Plan de Conservación de Áreas Sensitivas paraAdjuntas y Municipios Adyacentes (Sensitive Areas Conservation Plan for Adjuntas andAdjacent Municipalities) was approved by the Junta de Planificación of Puerto Rico(Puerto Rico Planning Board) in 2004. The plan created the biggest conservation districtin Puerto Rico to date—14,568 ha of land spread over 10 municipalities. It also createdPuerto Rico’s first biological corridor, joining Bosque del Pueblo with four otherimportant regional forest units (Guilarte, La Olimpia, Toro Negro and Tres Picachos).Special zoning was achieved through important campaigns and dialogue with the PuertoRico Planning Board, and this established special conservation districts, and preparedspecial guides for using non-authorised lands.These efforts culminated in the creation of the Puerto Rican Biosphere Reserve in the TierrasAdjuntas. Using the management protocols associated with UNESCO’s Natural Heritageprogramme, the Biosphere Reserve includes a mosaic of ecological systems comprising thecommunity-managed forests of Bosque del Pueblo and Bosque La Olimpia as core areas,along with privately-held transition and urban areas. DNER made Casa Pueblo communitymanager of the Puerto Rican Biosphere Reserve in 2005. Community management mustensure: (i) the conservation of genetic resources, species, ecosystems and landscapes; (ii)economic and human sustainable development of people living in the reserve; and (iii)research, education, training and observation to support this conservation and sustainabledevelopment. The guiding principle of the Puerto Rican Biosphere Reserve is that the localpopulation takes a constructive leading role and is not excluded from managing the land.As an integral part of the participatory management initiatives in the areas of transition,Casa Pueblo designed a programme called Reservas Forestales Familiares (Family ForestReserves).These reserves lie within the Biosphere Reserve but are in private hands.Thus,farmers and landowners, together with Casa Pueblo and the DNER, can manage land inways that will be harmonious with nature. This new community strategy supportslandowners’ own desire to conserve the environment. Initially, around 1,214 ha of landwere included as this type of reserve, representing more than 4% of the territory of theAdjuntas municipality. Instead of imposing prohibitions and bans, this plan encouragesgood management of agricultural properties, family forests, and sources of renewableenergy, and gives concrete suggestions on how to achieve this.Education for changeIn 2003, Casa Pueblo started an environmental education programme, the InstitutoComunitario de Biodiversidad y Cultura—ICBC (or the Biodiversity and CultureCommunity Institute). This was launched together with the Washington IrvingElementary Community School of Adjuntas and the University of Puerto Rico atMayagüez. It also operates with the support of parents, Casa Pueblo’s volunteers, univer-sity professors, scientists and artists, and with the participation of schoolchildren.ICBC-Casa Pueblo is an education programme that spans the elementary school level touniversity level, integrating co-operative education with community self-management,while promoting a humanist integrated learning in the “natural laboratories” of the10gatekeeper 137b: August 2008Puerto Rican Biosphere Reserve. From a foundation of practical experiences, it supportsthe harvesting of knowledge in order to promote change. The project offers individualtransformation through re-education. In other words, students learn to critically analysetraditional ideas of what development is, and of what conservation is (too oftencordoning off a “natural area” and never going near it or engaging with it), and then learnto value knowledge that might not necessarily be taught in a classroom.This knowledgeis then integrated with leadership to seek transformation at different scales. Casa Pueblobelieves that education is much more than simply learning to read and write.At the ICBCstudents engage with difficult concepts, learn about and preserve their own culture, anduse scientific investigation in different aspects of life.In addition to learning in the Bosque del Pueblo and Bosque La Olimpia, lessons areconducted in Casa Pueblo’s room of co-operative learning, research laboratory, hydro-ponics laboratory and plant nursery. An auditorium with access to real-timevideoconference enriches the educational experience through meetings with professorsfrom the university. The Lepidoptera Garden, weather station, solar energy system andCasa Pueblo’s other facilities all contribute to an inclusive and dynamic education. Morethan half of the students enrolled in the public school benefit from these programmesor other special activities, such as the annual arrival of the migratory bird and symbol ofBosque del Pueblo, Julián Chiví (Vireo altiloquus).One of the most outstanding contributions by student researchers in ICBC-Casa Pueblowas their participation in the development of a conservation plan for Adjuntas. This planincludes an ecological belt around the urban area, special protection of water basins, andconservation of the landscape.These students also took part in the process of promotingand acquiring the core area of 50 ha of land in the headwaters of Río Grande of Arecibo.During the summer, tens of students from high schools of coastal areas attend and resi-dential university courses are offered. With such programmes, Casa Pueblo promotes anacademic environment at several levels in the community while attracting scientists whowant to take part in its management activities. In 2007, Casa Pueblo strengthened therelationship between science and culture by establishing an artist residency programme:“humanising education through art”. Through agreements with the Instituto de CulturaPuertorriqueña (Puerto Rican Culture Institute) and Prinardi Gallery, Casa Pueblo hosted arenowned painter who lived at Casa Pueblo and offered painting classes to students of theWashington Irving Elementary School and the community in general. By strengtheningobservation of the surroundings, recognition of the diversity of forms and colours, andsensitivity to the nature around them, painting has contributed another facet to therounded leadership skills needed for protecting and using the environment.Renewable energy: increasing the reserve’s ecological servicesIn co-operation with the School of Engineering at UPR-Mayagüez, Casa Pueblo hasdeveloped a research and education programme on renewable alternatives for electricitygeneration, in order to eliminate dependence on sources of costly and non-renewableenergy resources such as oil, gas and coal. Since 1999,Casa Pueblo itself has operated withsolar energy, and has recently developed a system of solar water distillation. The ModeloThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution11de Interconexión de Energía Renovable para las Comunidades (Model of Interconnection ofRenewable Energy for Communities) is the first example of technical progress in PuertoRico in integrating renewable energy within communities.The community is transformingitself from energy consumer to energy producer—a supplier of clean energy in a setting ofsocial justice while reducing the environmental impact of burning fossil fuel.The supply of renewable energy to national electricity supply grids occurs in Europeancountries and in many states of the USA, but public policy in Puerto Rico supports amonopoly of non-renewable sources, thus undermining this option. Because Puerto Ricocurrently depends on fossil fuels for more than 99% of its energy, the Casa Pueblo modelconsists at this stage of installing photovoltaic systems which convert solar energy toelectricity that could then be fed into the country’s national distribution system. Duringthe day, unused solar energy would enter the network, while during the night householdswould use energy generated by other sources. This avoids the costs of storing energy inbatteries and the environmental costs of disposing of them. Further research on thistopic will investigate how much electricity generation based on fossil fuels may bereplaced with renewable generation in the communities and the value of CO2 emissionsprevented. In August of 2007, the government of Puerto Rico approved net metering, apublic policy change which will help the initiative to take off.Casa Pueblo will be the firstcommunity-based organisation with a state-of-the-art renewable energy “lab” thatmeets this new challenge. Carbon trading and other potential financial agreements arenow real possibilities for the community.What underlies Casa Pueblo’s success?One of Casa Pueblo’s most important achievements has been to mobilise support fromdistant areas in Puerto Rico and abroad to help Casa Pueblo improve the local economyand education. More than 20,000 people visit each year, making Casa Pueblo a nationalcommunity school. Poverty is a serious problem throughout Puerto Rico (nearly half thepopulation lives below the poverty level); a poverty of spirit and self-esteem is alsoprevalent. Many people suffer from the psychological consequences of a lack of gainfulwork. Puerto Rico’s traditional cultures are quickly vanishing to make way for American-influenced media, music and values. So entrenched is this, and so fundamental to many ofthe problems the community faces, that Casa Pueblo hopes through its work to invigoratepeople’s spirit, culture, knowledge and empowerment. Through its community-run coffeeenterprise and the massive amount of visitors it brings to the area each year (20,000 intoa municipality of 17-18,000 people),Casa Pueblo nourishes the economic wellbeing of thearea and serves as an example of a self-sustaining and well-run organisation. Through itsenvironmental campaigns, Casa Pueblo nourishes the area with unpolluted water andforests that will now be able to be enjoyed for generations to come. Through its contin-uous support for the local public school and initiatives for the community’s students, CasaPueblo nourishes the intellect, knowledge, and independence of the next generation.Moreover, through its myriad cultural activities each year, Casa Pueblo also nourishes thespirit of the people. For all of these reasons, Casa Pueblo has been cited as a model ofchange and hope in a world full of pessimism and empty of feasible alternatives.12gatekeeper 137b: August 2008Casa Pueblo’s successes have been achieved for three basic reasons:1. Casa Pueblo has gained prestige and recognition at local, national and internationallevels; in 2002, the founder and director of Casa Pueblo, Alexis Massol, won theInternational Goldman Environmental Prize. This prestige was acquired not withwords, but with decades of action in community struggle, transformation and victory.2. Casa Pueblo has consistently provided viable alternatives that are environmentallyhealthy, socially compatible, and economically feasible, and that also reinforce thevalues of Puerto Rican culture.3. Casa Pueblo’s strategies are coherent, well-planned and above all brave, carried out bymany people committed to the future of their homeland.Managing donor relationsToo often, management guidelines end up being dictated by the donor agencies or foun-dations, or at least compromise the direction and form of the recipient’s initiatives. Instead,external funds invested at community level should aim at strengthening communitymanagement, and not be a public relations exercise for external investors that deprives thetrue agents of change of their motivation and kudos. Independence from external influencehas been another important factor in Casa Pueblo’s success. Casa Pueblo’s large degree offinancial self-sufficiency has helped to ensure this. To date, donations from the co-operative sector, some private entities, and from the people themselves have funded CasaPueblo’s community activities. Casa Pueblo’s organisational governance and track recordmean that external groups contribute with matching funds or donations, but withoutattempting to impose an agenda or seek public recognition. All donors have understoodthat rather than dictating local agendas they would be promoting local agendas.Difficulties faced in community-based self-managementCasa Pueblo decided, from the beginning, to develop a community-based managementstyle of its own. However, this decision generated repression from the state, isolation,and attacks from opportunistic parties and politicians who wanted to maintain anunequal relationship between community and government. Casa Pueblo’s opposition tomining also caused conflict with those sectors which supported mining or which resistedchange to public policy provoked by grassroots groups. Lack of faith in the ability of thecommunity to attain empowerment and leadership contributed (and maybe stillcontributes) to a certain reluctance among some sectors of the community to reallycommit to change.These mixed feelings led to marginalisation and conflict at all levels,including within the traditional family structure. By diversifying the range of itssupporters, including more and more people who had a stake in the issue, and throughgaining the trust of the people through openness, transparency, and inclusion of thecommunity in the decision-making process, Casa Pueblo eventually overcame theseThe Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution13difficulties. In fact, the strength of character of the organisation and its members wasbolstered as a result of such repression and conflict.None the less, resistance, arrogance, inefficiency and idleness of government lawyersand administrators in key offices of the DNER delayed, obstructed and put at risk theinitiatives that later positively and effectively changed the country’s public forest policy.Currently, intermediate levels of government and sectors that feel threatened by thescientific use of forests and by the effectiveness of the forest management seem to bethe new constraints to Casa Pueblo’s initiatives.One of the enduring obstacles is Puerto Rico’s colonial political status, which condemnsthe country to international isolation. Exclusion from international fora and globalcommunity networks, as well as the lack of access to external funds from internationaldonors and programmes, hinders important development and expansion of the organi-sation. Casa Pueblo continues to struggle to defeat such international exclusion; it isslowly winning, but it requires more external understanding and support. After a longprocess the Puerto Rican Biosphere Reserve was recognised in November of 2007 as anew unit in the Latino-American and Caribbean Network (LAC-Net) of the Model ForestNetwork. This important designation—the result of a sustained bottom-up process —has begun to reverse Puerto Rica’s international isolation.Next stepsMost groups that appear to fight specific battles often disappear once the principal issueis resolved. Institutional evolution is invariably needed if the organisation is to keepcontributing to the community and instigating change within society.The fact that CasaPueblo has thrived for over 28 years is evidence that internal change for social transfor-mation can work. From the mines to the forest; from the forest to the house; from thehouse to the school; from the school to the economy; from the economy to the reserve;from the physical reserve to the psychological freedom that enables us to embracedestiny marked by community victories.So what is next for Casa Pueblo?The first step is to strengthen and protect the goals achieved to date. On 12 May 2007the Casa Pueblo Trust consolidated a legal structure that will protect its assets in perpe-tuity. This measure ensures that the properties and many projects will continue to behandled appropriately in the future, and that private areas of high ecological value willbe protected through non-governmental and self-determined initiative.The second step is to improve the management structure to make inter-generationalchange easier. Casa Pueblo has amended the Board of Directors to include new local andnational actors, and created a supervisory technical committee as well as a ManagementBoard for the Puerto Rican Biosphere Reserve, composed of scientists, artists, traders,government, teachers, students, universities, workers, farmers and others. To reinforcethese developments, Casa Pueblo has formed a stronger alliance with the University ofPuerto Rico by appointing a permanent professor at Casa Pueblo.14gatekeeper 137b: August 2008Finally, horizontal growth will be one of the most important challenges in Casa Pueblo’snext stage. The new working structure aims at multiplying the stakeholders of theproject and at the same time enabling them to become actors in a process of socialtransformation within nearby and distant communities. The organisation will rely uponthe participation of farm owners within the Puerto Rican Biosphere Reserve, who will bepart of the programme of Family Forest Reserves; continuous educational programmesin the arts and sciences; and the promotion of the production of renewable clean energy.Instead of a top-down funding model paying for community actions, the intention is toestablish a financial structure that should enable the community itself to catalyse othercommunity initiatives with their own community-led agendas. Seeking alternative formsof financing and sustainable economic ventures will enable Casa Pueblo to achieve thiskind of scaling-up in the future.With these goals in mind, Casa Pueblo foresees an optimistic future.The launch in 2008of Radio Casa Pueblo WOKI 1020 AM, the first community-based radio station on theisland, has certainly catalysed further changes as new economic and educational oppor-tunities emerge to promote Casa Pueblo’s role—a local organisation influencing nationaland indeed international agendas.The Evolution of Casa Pueblo, Puerto Rico: From Mining Opposition to Community Revolution1516gatekeeper 137b: August 2008110. Risking Change: Experimentingwith Local Forest ManagementCommittees in Jamaica. 2003.Tighe Geoghegan & Noel Bennett111. Contract Farming in India: Impactson women and child workers. 2003.Sukhpal Singh112.The Major Importance of ‘Minor’Resources:Women and PlantBiodiversity. 2003.Patricia Howard113.Water For All: Improving WaterResource Governance in SouthernAfrica. 2004.Emmanuel Manzungu114. Food Industrialisation and FoodPower: Implications for food gover-nance. 2004.Tim Lang115. Biodiversity planning:Why andhow should local opinions matter?2004.Sonja Vermeulen116. Laws, lore and logjams: Criticalissues in Indian forest conservation2005.Madhu Sarin117. Adapting to Climate Change inEast Africa: A strategic approach 2005.Victor A. Orindi and Laurel A. Murray118. Facing up to Climate Change inSouth Asia. 2005.Mozaharul Alam and Laurel A. Murray119. State Policies and Land Use in theChittagong Hill Tracts of Bangladesh.2006.Golam Rasul120. Organic Cotton: A NewDevelopment Path for AfricanSmallholders? 2006.Simon Ferrigno, Saro G. Ratter,Peter Ton, Davo Simplice Vodouhê,Stephanie Williamson and John Wilson121.The Market for Voluntary CarbonOffsets: A new tool for sustainabledevelopment? 2005.Nadaa Taiyab122. Getting the Message Across:Promoting ecological agriculture inBangladesh. 2006.Dipankar Datta and Kamal Kar123. Climate Change and DevelopmentLinks. 2006.Saleemul Huq, Hannah Reid and Laurel A. Murray124. Mysteries and Myths: De Soto,property and poverty in South Africa.2006.Rosalie Kingwill, Ben Cousins,Tessa Cousins, Donna Hornby,Lauren Royston and Warren Smit125.Working Together: Forest-linkedsmall and medium enterprise associa-tions and collective action 2006.Duncan Macqueen, Sharmistha Bose,Septi Bukula, Cornelius Kazoora, SharonOusman, Noemi Porro and HorstWeyerhaeuser126. Seed diversity in the drylands:Women and farming in South India.2006.Carine Pionetti127. State-farmer partnerships for seeddiversity in Mali. 2006.Didier Bazile128. Mainstreaming participatoryforestry within the local governmentreform process in Tanzania. 2006.Tom Blomley129. Banishing the Biopirates: A newapproach to protecting traditionalknowledge. 2006.Krystyna Swiderska130. A People’s Plan for BiodiversityConservation: Creative strategies thatwork (and some that don’t). 2006.Tejaswini Apte131. Legislators and Livestock:Pastoralist parliamentary groups inEthiopia, Kenya and Uganda. 2007.John Morton, John K. Livingstone andMohammed Mussa132.Who benefits from land titling?Lessons from Bolivia and Laos. 2007.Susana Lastarria-Cornheil133. Keeping CAMPFIRE Going: Politicaluncertainty and natural resourcemanagement in Zimbabwe. 2007.Everisto Mapedza134. Land Reform and Rural Territories:Experience from Brazil and SouthAfrica. 2008.Julian Quan135. Democratising TechnologyChoices? European Public Participationin Agbiotech Assessments. 2008.Les Levidow136. Underfed, Underpaid andOverlooked:Women, the Key to FoodSecurity in South Asia. 2008.Nira Ramachandran137. Understanding and Supporting theRole of Local Organisations inSustainable Development. 2008.David Satterthwaite and Gabriela Sauter137a. Association ANDES: ConservingIndigenous Biocultural Heritage in Peru.2008.Alejandro Argumedo and Tammy Stanner137b.The Evolution of Casa Pueblo,Puerto Rico: From Mining Opposition toCommunity Revolution. 2008.Alexis Massol-González,Avril Andromache Johnnidis and Arturo Massol-Deyá137c: IIED-América Latina: neighbour-hood credit funds in Buenos Aires,Argentina. 2008.Florencia Almansi and AndreaTammarazio137d.The Organisation of RuralAssociations for Progress, Zimbabwe:Self-reliance for Sustainability. 2008.Dumisani Nyoni137e.The Pastoral Women’s Council:Empowerment for Tanzania’s Maasai.2008.Maanda Ngoitiko137f:The Urban Resource Centre,Karachi. 2008.Arif Hasan.PREVIOUS GATEKEEPER PAPERSThe Gatekeeper Series has been published since 1987. Here we list the most recent titles. These, plus many earlier titles, can bedownloaded free from our website: www.iied.org/pubs/SUBSCRIBING TO THE GATEKEEPER SERIES To receive the Gatekeeper Series regularly, individuals and organisations can take out a subscription. Subscribers receive nineGatekeeper papers a year. Subscriptions are free. For more details or to subscribe contact: IIED, 3 Endsleigh Street, London,WC1H 0DD,UK. Email gatekeeper@iied.org Tel: +44 020 7388 2117; Fax +44 020 7388 2826, or complete the online order form at www.iied.orgOTHER IIED PUBLICATIONS For information about IIED’s other publications, contact: EarthPrint Limited, Orders Department, P.O. Box 119, Stevenage,Hertfordshire SG1 4TP, UK Fax: +44 1438 748844 mail to: orders@earthprint.co.uk There is a searchable IIED bookshop database on: www.iied.org/pubsSUBMITTING PAPERS TO THE GATEKEEPER SERIES We welcome contributions to the Gatekeeper Series from researchers and practitioners alike.The Series addresses issues of interest to policy makers relating to the broad area of sustain-able agriculture and resource management. Gatekeepers aim to provide an informed briefingon key policy issues in a readable, digestible form for an institutional and individual reader-ship largely comprising policy and decisionmakers within aid agencies, national governments,NGOs and research institutes throughout the world. In addition to this primary audience,Gatekeepers are increasingly requested by educators in tertiary education institutions,particularly in the South, for use as course or seminar discussion material.Submitted material must be of interest to a wide audience and may combine an examina-tion of broad policy questions with the presentation of specific case studies. The papershould conclude with a discussion of the policy implications of the work presented.Style Gatekeepers must be short, easy to read and make simple, concise points.• Use short sentences and paragraphs.• Keep language simple.• Use the active voice.• Use a variety of presentation approaches (text, tables, boxes, figures/illustrations, bullet points).• Length: maximum 5,000 words Abstract Authors should also include a brief summary of their paper – no longer than 450 words.Editorial process Please send two hard copies or an electronic version of your paper. Papers are reviewed bythe editorial committee and comments sent back to authors.Authors may be requested tomake changes to papers accepted for publication. Any subsequent editorial amendmentswill be undertaken in consultation with the author. Assistance with editing and languagecan be provided where appropriate. All illustrations and graphs, etc. should be suppliedseparately in their original format (e.g. as jpeg files) as well as being embedded withindocuments. This will allow us to modify the images where necessary and ensure goodreproduction of the illustrations in print.Papers or correspondence should be addressed to:Gatekeeper Editor Sustainable Agriculture, Biodiversity and Livelihoods Programme IIED, 3 Endsleigh Street,London WC1H ODD,UKTel:(+44 020) 7388 2117Fax: (+44 020) 7388 2826e-mail: gatekeeper@iied.orgThe Sustainable Agriculture, Biodiversity and Livelihoods (SABL)Programme coordinates the editorial process for the GatekeeperSeries. The Programme seeks to enhance and promoteunderstanding of environmental sustainability and equity in agri-food systems and the use of biodiversity. It emphasises closecollaboration and consultation with a wide range of organisationsand takes a multidisciplinary approach. Collaborative researchprojects are aimed at identifying the constraints and potentials ofthe livelihood strategies of marginalised groups who are affectedby ecological, economic and social change. These initiatives focuson the development and application of participatory approachesto research and development; resource conserving technologiesand practices; collective approaches to resource management; thevalues of wild foods and biodiversity; rural-urban interactions;strengthening citizen voice and agency in policy processes, andpolicies and institutions that work for sustainable agriculture andbiodiversity-based livelihoods.SABL is part of the Natural Resources Group (NR Group) at IIED,which encompasses two other programmes: Drylands and Forestryand Land Use. The NR Group and its partners work to enablegreater participation of marginalised groups and to promote moresustainable and equitable patterns of land and natural resourceuse. We build partnerships, capacity and wise decision-making forfair and sustainable use of natural resources. Our priority is thecontrol and management of natural resources and otherecosystem services by the people who rely on them, and on thenecessary changes needed at international and national level tomake this happen.ISSN 1357-9258Design: Piers AitmanPrint: TARA, an enterprise of Development Alternatives Group100% recycled paper handcrafted by tribal women in IndiaInternational Institute for Environment and Development3 Endsleigh Street, London WC1H 0DDTel: (+44 020) 7388 2117Fax: (+44 020) 7388 2826E-mail: sustag@iied.orgWebsite: www.iied.org', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/14857IIED_2024-04-05-20-24-17/14857IIED_2024-04-05-20-24-17.pdf', '', 1, 1, 1, 1, 2, '2024-04-06 08:24:32');
INSERT INTO `Documents` (`id`, `title`, `author`, `content`, `rena`, `theme`, `doctype_id`, `country_id`, `institution_id`, `lenguage_id`, `user_id`, `created_date`) VALUES
(3, '(anonymous)', '(anonymous)', 'Satnam SinghAmber PetersenEnglish 100June 18th, 2018Negative Impacts of Fast FoodIn this modern era fast food consumption has become a global phenomenon (Joseph et al. 13). Peopleare crazy after fast food, especially young children. The popularity of fast food in this age ofurbanization has been attributed to quick preparation, great taste, affordable price and convenience offinishing a meal within no time (Joseph et al. 13). Apart from these, advertising has played a key role inattracting people especially young adults or children. However, the growing demand of fast foodconsumption leads to obesity, sugar and several health-related problems (Mattsson and Helmersson117). Therefore, our main concern is the modelling of attitude and consumption of young fast foodeaters. In the upcoming paragraphs I will discuss the negative impact of fast food on children, diseasesthat can occur due to fast food and prevention methods to reduce this problem. At the end I willsummarize all these points I mentioned above and my own recommendation or opinion.Fast food can be attractive to children for a number of reasons, including taste, affordable price andconvenience. Fast food particularly attracts children because most of the time they ignore the healthconsequences of their eating habits. Therefore, children are the main target of fast food companies.“Author’s research found that youngsters who watch more television are more susceptible to unhealthyeating habits as compare to others who watch minimally” (Qtd in Joseph et al. 16). This is because thecurrent food advertising rarely promotes healthy choices and rather promotes frequent consumption ofunhealthy foods (Joseph et al. 16). According to a study in India children, despite knowing the harmfuleffects, continued to eat fast foods and for reasons like taste preferences, and an ardent desire to quickeat (Joseph et al. 16). Moreover, fast foods are gaining popularity in nuclear families because workingparents have less time for meal preparation at home (Joseph et al. 16). This tendency can bedetrimental because children pickup these unhealthy eating habits early in life. Studies have shown thatchildren who were overweight or obese were significantly greater among most frequent users of fastfoods (Joseph et al. 16). Joseph et al.’s study in Baroda India, reported that almost 96 % of peoplewere aware of health hazards due to fast food still continued to eat fast foods and only 65 % people feltthe need to control its usage (Joseph et al. 16). These statistics proved that people ignore orcompromise with the health hazards that can occur due to fast food when they get addicted to fastfoods. For example, many people still continued to do smoking even they aware about the negativeimpacts of smoking when they get addicted to fast food. Therefore, children should make aware aboutthe dark side of fast foods before they get addicted to junk food. All these points make it clear that howchildren get addicted to fast food and how junk food adversely effects public healthStudies have shown that children who were overweight or obese were significantly more among mostfrequent users of fast foods (Joseph et al. 16). A number of diseases have been linked to overweightand obesity. Moreover, the Centers for Disease Control reports that overweight and obese individualsare at increased risk for hypertension and stroke, Type 2 Diabetes, coronary heart disease, andpsychological disorders such as depression and low self-esteem (Adams 300). Adams study reportedthat. “an estimated 300,000 death per year in the United States can be attributed to obesity, and therisk of death rises sharply with increasing weight” (300). For example, high blood pressure a leadingcasual factor in strokes is twice as common in obese individuals as compared to those who are at anormal weight (Adams 300). Furthermore, obesity or overweight also double the risk of Type 2Diabetes to twice as compare to others who have not experienced weight gain (Adams 300). Inaddition, change in disease patterns are also evident (Adams 300). For example, in the past Type 2Diabetes was considered and adult disease, but nowadays it is quite common among children who areoverweight or obese. Not only this, but obese or overweight children are less likely to go to the gym orplayground and are less active compare to others. All these points and statistics show that fast foodaddiction leads to obesity and causes many health-related problems.Increased consumption of fast food has many adverse effects on public health therefore it is highlyimportant to address the causes of fast food addiction and approach to some possible ways to reducethis problem. As mentioned above, advertisements especially advertisements appear on TV play acrucial role in promoting unhealthy foods. Fast food companies target young children and makestrategies to attract young children because they prefer taste as compared to health. Therefore,advertisements guidelines related to quality of food products in mass media needs formulation andstrict implementation (Joseph et al. 16). Moreover, children spend considerable time in school and atthat time they are away from their families as well as in a less restricting environment about eatingchoices compared to home (Joseph et al. 16). Therefore, students should be taught healthy eatinghabits in schools. As majority of students are eating fast food outside school and in the homeenvironment it would be difficult to monitor their habits (Joseph et al. 16). Hence awareness abouthealth hazards and self-motivation to adopt healthy eating behavior appears to be the best solution tothis problem. Apart from this, healthy food should be more affordable because one of the reasonsbehind fast food popularity is that it is cheap and affordable. For example, if healthy food is moreaffordable people can approach healthy food instead of fast food.To conclude, after addressing all the points mentioned above it can be said that there is a need fornutrition counseling to bridge the gap between knowledge and practice about healthy eating behavior.Fast food addiction is quite common among young adults and main reason behind childhood obesity.Moreover, junk food is also responsible for many health hazards. Therefore, the views of children onfactors at home which affect their desire to eat healthy foods need to be understood and addressedappropriately. Parents must set an example themselves by not eating fast foods and improving homefood to support discouragement of fast foods. Schools can also play vital role to mitigate this problem offast food addiction by making people aware about the adverse effects of fast foods. In my opinion,combine efforts of parents and teachers may be beneficial approaches for addressing fast foodaddiction and reduce the consumption of fast food more broadly.Works citedJOSEPH, NITIN, et al. \"Fast Food Consumption Pattern and Its Association with Overweight amongHigh School Boys in Mangalore City of Southern India.\" Journal of Clinical & Diagnostic Research, vol.9, no. 5, May 2015, pp. 13-17. EBSCOhost,doi:10.7860/JCDR/2015/13103.5969.Mattsson, Jan and Helge Helmersson. \"Eating Fast Food: Attitudes of High-School Students.\"International Journal of Consumer Studies, vol. 31, no. 1, Jan. 2007, pp. 117-121. EBSCOhost,doi:10.1111/j.1470-6431.2006.00576.x.Adams, Ronald. \"Fast Food, Obesity, and Tort Reform: An Examination of Industry Responsibility forPublic Health.\" Business & Society Review (00453609), vol. 110, no. 3, Fall2005, p. 297. EBSCOhost,ezproxy.cotr.bc.ca/login?url=https://searchebscohostcom.ezproxy.cotr.bc.ca/login.aspx?direct=true&db;=edb&AN;=17856753&site;=eds-live..', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/11111_2024-04-05-20-29-49/11111_2024-04-05-20-29-49.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:29:50'),
(4, '(anonymous)', '(anonymous)', 'Allan DewijnAmber PetersenEnglish 1002018-06-18Research PaperOver the history of Canada there have been many tragedies and on-going issues that continue toplague the First Nations living in this beautiful country. The generational trauma and re-victimization offamilies through the decades of residential schools, along with the stripping of culture, has lead to FirstNations being victims of another great tragedy: the over-representation of Aboriginals in our CanadianCriminal Justice System (CCJS). The over representation also carries into the proportion of custodyamong First Nations. The Department of Justice found “…indigenous adults in custody was about 9times higher than their representation in the adult population…” (Department of Justice). In BritishColumbia (BC), sentenced Aboriginals were five times higher then other races. (La Prairie, 187). Theover representation of Aboriginals is a very clear issue that has lead to much research being done inthe hopes of finding causes that then lead to solutions. This paper will argue that Status Aboriginals areover represented in the Canadian Justice System due to low socioeconomic status, over dependencyon welfare, and growing stress in urban areas.A paper written by Carol La Prairie called “Aboriginal over-representation in the criminal justice system:A tale of nine cities” attempts to address some of the major issues that are influencing this overrepresentation of aboriginals in Canada. One of the major findings that she found in her studies duringthis research was the impact that low socio-economic status had on Aboriginals. Not all Aboriginals arealike, but rather the Status Aboriginals were significantly more likely to be disadvantaged than thenon-registered Aboriginals. The location of where the offences were happening tended to be in urbanareas which was a contributing factor. Carol found the location of crimes not as important as the factthat these Status Aboriginals committing the crimes were raised on reserves. The larger numbers oflow socioeconomical status people who grew up on reserves were more likely to be unemployed withthe youth between the ages of 15 to 19, being more at risk of offending and beginning a life of crime.Carol questioned if the same number of crimes were being committed on reserves, but perhaps theyare being dealt with differently and not ending up in the Canadian Justice System.An interesting point of research that was introduced by researcher Jeremy Hull and built upon by CarolLa Prairie, was the findings of how the economic dependency that Status Aboriginals raised onreserves, have on the government. With limited job opportunities, Hull points out that government aid isnot helping but rather damaging their lives as it does not improve their socio-economic levels but onlyraises their odds of committing crime. Hull discusses how the dependency that the Aboriginals have onthe Canadian government effects their entire community and causes the reserves to produce littlewealth. Hull states “…the number of business-owners on reserves is very small, and the number ofworkers is also relatively small and is concentrated in public sector administration and services” (Hull).Ironically, education levels have increased in both the grade 12 diplomas and post-secondary degreesfor status Aboriginals, yet the high levels of welfare continue (Hull, 46). This then questions the qualityof education standards in reserve schools that the government is providing (Hull, 48). High levels ofwelfare dependency for status Aboriginals seems to be increasing despite government interventions (p.54). Hull believes the easiest solution is to bring jobs into the communities whether it is stores,construction, or labour jobs. This is easy to envision, but the execution is not as simple as Hull pointsout the level of education, resources, and independence may not be in place to build the economywithin the reserve.With the lack of work on reserves, status Aboriginals were moving to urban communities to build theirlives. When researching where crimes were committed, Carol La Prairie found nine urban cities locatedin the prairie provinces and Ontario that had the highest over representation rates (La Prairie). Theyalso found that in Canada “…more than half (54%) of the aboriginal youth lived in a city during the twoyears prior to the current admission, while 23% lived on a reserve” (La Prairie). No matter where thecrimes are being committed, the common link between those entering the Criminal Justice System, wasbeing raised as a status Aboriginal typically on reserve. Did the change of life style and customs createthe stressors pushing the status Aboriginals towards committing crimes? The higher costs of living andlarger populations may also be creating pressure on status Aboriginals in urban areas. The distinctionbetween on reserve crime and off reserve crime is a very important finding and may not be surprising tosome. Carol points out that higher crime rates within urban areas, compared to a lower on reservecrime rates may be misleading. The explanation may be in how crime is dealt with on reserve differentlythen municipal non-reserve areas, keeping the status Aboriginals out of the Canadian Justice System(La Prairie).There are those that argue that the Aboriginal people should be accommodated within the CanadianCriminal Justice System as they have unique histories, practices, and beliefs. Giving control over theirown justice within their communities is an ongoing argument and “cultural defence” for Aboriginalpeoples who have committed crimes in the past (Widdowson, Frances and Howard). The impact ofgiving leniency towards Aboriginals who have committed crimes may take the offenders out of the jails,but at what price? “This means that accommodating aboriginal cultures could actually result in anincrease in the number of offences perpetrated, as there are fewer deterrents against native criminality”(Widdowson, Frances and Howard).The over representation of Aboriginals in Canada continues to be a phenomenon that researcherscontinue to study. Finding a solution that can repair all the damage that has been caused to the FirstNations of Canada, while also attempting to allow their communities to grow and become independent,may require much more future research. As possible solutions are developed to help influence changein government polices, steps forward are being taken to improve the lives of millions of Aboriginals. Arecent change that has become a very promising and effective strategy, is the introduction ofRestorative Justice (RJ) in the Criminal Justice System. Stemming from traditional First Nations culture,RJ seeks to repair the offender, victim, and community instead of punishing and removing the offenderfrom our society (Ministry of Public Safety and Solicitor General, & Ministry of Justice). RJ focusesmore on rehabilitating and healing while meeting the victims needs and engaging the communities. Ithas been a step in the right direction for Aboriginals across Canada. To build on to these researcharticles, it would be interesting to investigate the generational trauma Aboriginals have faced and howalcoholism may be affecting their communities. It would also be interesting to see how dry reservescompare to non-dry reserves in crime rate. Evidence shows that the contributing low socioeconomiclevels in Aboriginal families, a dependency on the Canadian government for welfare, and a growingpopulation within urban areas, all being connected like a giant web which contribute to the overrepresentation of Aboriginals. The complex question as to the causes and solutions to the high rates ofover representation of status Aboriginals in the Canadian Criminal Justice System, has yet to beanswered.ReferencesDepartment of Justice. “JustFacts.” Government of Canada, Department of Justice, ElectronicCommunications, 14 Feb. 2018, www.justice.gc.ca/eng/rp-pr/jr/jf-pf/2017/jan02.html.Hull, Jeremy (2001) Aboriginal People and Social Classes in Manitoba. Ottawa: Canadian Centre forPolicy Alternatives.La Prairie, C. (2002). Aboriginal over-representation in the criminal justice system: A tale of nine cities.Canadian Journal of Criminology, 44(2), 181-208.Ministry of Public Safety and Solicitor General, & Ministry of Justice. (2018, March 21). RestorativeJustice - An Overview. Retrieved fromWiddowson, Frances and Albert Howard. Disrobing the Aboriginal Industry : The Deception behindIndigenous Cultural Preservation. MQUP, 2008. EBSCOhost, ezproxy.cotr.bc.ca/login?url=https://search-ebscohost-com.ezproxy.cotr.bc.ca/login.aspx?direct=true&db;=nlebk&AN;=404065&site;=eds-live.https://www2.gov.bc.ca/gov/content/justice/criminal-justice/bcs-criminal-justice-system/understanding-criminal-justice/restorative-justice', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/Allan Dewij1_2024-04-05-20-31-37/Allan_Dewij1_2024-04-05-20-31-37.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:31:38'),
(5, '(anonymous)', '(anonymous)', 'Baljinder SinghCaley EhnesENG100-0824 October 2018Female Feticide in IndiaThis research conversation will address the question: What are the impacts of killing female infants onsocial and economic spheres of India? Even educated families are practicing abortions due to culturaland religious factors; moreover, they are getting political support with the help of Bharativa Janta Party(BJP) as they support the Hindu religion. Furthermore, some people prefer a son over a daughter andthey utilize fetal to determine the gender ultrasound which is now more available; hence, there is anincrease in selective abortion. However, because of mortality the estimated imbalance in the child sexratio of 0-6 years is significantly smaller. The following articles, will be analyzed: “Modernization,Religion and Female Feticide in India” (2016), written by Riaz Hassan and “Trends in SelectiveAbortions of Female in India: Analysis of Nationally Representative Birth Histories From 1990 to 2005and Census Data From 1991 to 2011” (2011), written by Prabhat Jha, Maya A Kesler, Rajesh Kumar,Faujdar Ram, Usha Ram, Lukasz Aleksandrowicz, Diego G Bassani, Shailaja Chandra, Jayant KBanthia. Both of these articles reference, The National Family Health Survey to explain that, India’sfemale sex ratio is going down tremendously because of familial, cultural, religious, and personalbeliefs. This research essay will analyze the above articles and explain the connection between them. Iwill also discuss how citations are important.In the essay “Modernization, Religion and Female Feticide in India,” (2016), Hassan analyzes theresearch on dropping female economic progress in India and discusses the latest statistics,investigates the statistical patterns, and provides ongoing exploration on the differential child deathrates in India. In addition, Hassan investigates the marvel of ‘missing women’ in India by concentratingparticularly on the patterns in sex proportions in India in the course of recent years. Hassan’s articlecites Amartya Sen’s article titled by “More Than 100 Million Women are Missing” which explains bydoing a comparison with other country’s, like Pakistan’s and Bangladesh’s sex ratio (12). Senevaluated that in the mid 2000s India had 37 million missing women which is the second largestnumber on the planet, but fortunately wellbeing and welfare open arrangements in India have broughtabout decreasing female burden in mortality lately (Sen qtd.in Hassan 12). Hassan purpose is to scalethe issue of particular female fetus removal in order to analyze urgent open arrangements andintercessions to stop the act of planned specific sexual orientation related abortions which are now illicitunder the current Indian Laws (15). The purpose of Hassan article is to make them aware what ishappening in their country and how they can help to decrease such happenings; moreover, doctors arethe ones who are practicing abortion rather they should be one who save lives. Given the fact that thisarticle was published in the Journal of Management and Public Policy in this article Riaz is writing to anaudience of women rights groups, progressive political parties, and doctors.In the essay “Trends in Selective Abortions of female in India: Analysis of Nationally RepresentativeBirth Histories from 1990 to 2005 and Census Data from 1991 to 2011” (2011) Jha et al. explain thatthe abortion of female fetuses is common in India, particularly in urban areas by completing a surveyand trying to find history behind this happening. Jha et al. support their claim citing by the NationalFamily Health Survey that specific fetus removal of females in India has developed in the previous twodecades and records developing unevenness between the quantities of female to boys aged 0-6 years(1926). Mothers in rich households are more educated in the last 10 years as compared to mothers inpoor households, they prefer to know if the first baby is a boy with the help of fetal ultrasound (1921). Inaddition, the fundamental measurement was the contingent sex proportion of “second-order births aftera first born female” (14). Jha et al’s purpose is to enlighten the result of the survey and show howsignificantly the female sex ratio fell compared to males. Fetal ultrasound is practiced for the purpose ofselective abortion in order to make people realize how they are disrespecting and killing infants beforethey enter this world (1921). Given the fact that this was published in www.thelancet.com which is amedical journal, Jha et al. are writing to an audience of doctors, nurses, and gynecologist because theyare the ones who are making this happen and help to reduce female feticide by not supporting selectivesex abortion.The article written by Hassan cites Jha et al. to discuss evidence based on statistics in relation to thepractice of selective female abortions in India (14). Hassan talks about the increasing difference in thenumber of males to females and how abortion practice is utilizing ultrasound in a negative way. Jha etal. support Hassan by proving in the research that fetal ultrasound became very common and educatedmothers from urban areas are doing such practice in order to prove his point Jha et al. did researchwhich proves son is the preference compared to a baby girl. The relationship between both articles isthe research of selective sex ratio abortion practiced in India and how religion, value and beliefs ofpeople becoming victim for female growth.In my final paper, I will discuss about females are victims of parents who feel strongly about sexpreference. Educated mothers are getting fetal ultrasounds done to determine the sex of their child.Moreover, the sex ratio is decreasing because of social and economic inequality. As per myperspective, women face judgmental behavior when they have not even entered the world. Women areequally as capable as men and based on caste and creed people practice child mortality trends. Thesesources will support my final paper because it proves India is facing a huge imbalance in sex ratio asper the research. In urban areas, stay at home women are getting educated in urban areas comparedto the past, but their ideas about gender preference is still the same and that is why they are gettingselective abortion of females. The National Family Health Survey clearly explains in both articles thesex ratio of female in Indian states and territories is missing by 7.9 % and which is a huge tragedy (11).Citation is vital and helpful for students as well as the teacher and helps in avoiding plagiarism becausethis proves we have the relevant evidence and it’s our own work. Additionally, another crucial part is ithelps in doing relevant research based on the first citation. As mentioned in class discussion I followedthe steps by beginning with a general topic brainstorming and freewriting and also mapmaking whichhelped me in writing relevant information about this topic. Practice of citation and avoiding plagiarismaspects makes for work successful.Work CitedHassan, Riaz. “Modernization, Religion and Female Feticide in India.” Journal of Management & PublicPolicy, vol. 8, no.1, 2016, pp. 11–20. EBSCOhost, ezproxy.cotr.bc.ca/login?url=https://search.ebscohost.com/login.aspx?direct=true&db;=bth&AN;=121286040&site;=eds-live.Jha, Prabhat, Maya A Kesler, Rajesh Kumar, Faujdar Ram, Usha Ram, Lukasz Aleksandrowicz, DiegoG Bassani, Shailaja Chandra, Jayant K Banthia. \"Trends in Selective Abortions of Girls in India:Analysis of Nationally Representative Birth Histories From 1990 to 2005 and Census Data From 1991to 2011.\" The Lancet, vol. 377, no. 9781, 2011, pp. 1921-1928. Google Scholar,doi.org/10.1016/S0140-6736(11)60649-1', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/baljinder conversation final_2024-04-05-20-40-38/baljinder_conversation_final_2024-04-05-20-40-38.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:40:40'),
(6, '(anonymous)', '(anonymous)', 'Brynn RudykBrittany RhodesEnglish 100-0424 October 2018Research Conversation: English 100How do addiction and mental illness interact with one another? Is one the result of the other or are theycontributing factors to the likelihood of either happening? It is my goal to establish whether or notdepression is a key figure in the Opioid Crisis. My research conversation will discuss and examine thefollowing academic journals, “Opioid Crisis: No Easy Fix to Its Social and Economic Determinants”(2018) Dasgupta, Nabarun, Beletsky, Leo, and Ciccarone, Daniel and “The relationships of childhoodtrauma and adulthood prescription pain reliever misuse and injection drug use” (2016) Quinn, Kelly,Boone, Lauren, Scheidell, Joy D., Mateu-Gelabert, Pedro, McGorray, Susan P., Beharie, Nisha, andCottler, Linda B. Through my research I aimed to investigate what has catalyzed widespread addictionand the increased potential for overdose and death. But in order to better ones understanding of thiscomplex and somewhat controversial issue, it is essential to establish and identify the relationshipbetween both cause and effect.In the article “Opioid Crisis: No Easy Fix to Its Social and Economic Determinants” (2018) Dasgupta,Nabarun, Beletsky, Leo, and Ciccarone, Daniel assert that the Opioid Crisis is a driven by botheconomic and societal pandemonium (182) and is accompanied by personal, behavioural and geneticfactors (185). Dasgupta et al. identify the blame and scrutiny physicians and pharmaceutical companiesexperience due to the vast majority of the public believing that medical professions are in pursuit ofpersonal gain (182). When insurance providers restricted coverage for therapy, pharmaceuticalcompanies were presented with an opportunity to capitalize on the lucrative market of chronic pain(182). Following the decline of prescribing opioid analgesics with the goal of lowering the rate ofoverdoses, the amounts of overdoses actually increased elucidating that lowered dispensing of thedrug can’t be the right solution (Dasgupta et al. 183). Although, Dasgupta, Beletsky and Ciccarone areaware of what society commonly accepts as the force that sparked the Opioid Crisis, they urge us torecognize the other role that opioid analgesics can play; a means of escape for those whom haveendured despair— hardship and trauma (182). They are writing to medical field professionals that areresponsible for prevention, intervention and rehabilitation with the interest of proactivity and recovery(Dasgupta et al. 185). Dasgupta et al. stress the importance of educating health care professionals toguarantee proper treatment of personal wellness and implementing regular medical check-ups andconsistent monitoring of those affected by mental illness and addiction (185). Dasgupta et al. believethat by acknowledging causative reasons of this epidemic will help in promoting collective change(185).In the scientific health journal “The relationships of childhood trauma and adulthood prescription painreliever misuse and injection drug use” (2016) Quinn, Kelly, Boone, Lauren, Scheidell, Joy D.,Mateu-Gelabert, Pedro, McGorray, Susan P., Beharie, Nisha, and Cottler, Linda B. contend that traumais the key motivator for misuse of prescription pain relievers (190). Multiple graphs and statistics areimplemented throughout the source emphasizing a variety of reasons and types of trauma and howthey contribute to such a complex issue that has impacted so many. Their compassionate approach tothe crisis with focussed efforts on proactive measures and sustainable treatment would aid in theresolution to this epidemic (Quinn et al. 190). Quinn et al. demonstrate how effective methods of copingand better alternatives to prescribed pain relievers would be a huge success in preventative treatmentprograms (197). The urgency of treatment could be crucial to the fate of a person; there is a highchance of people who abuse prescription pain reliever analgesics to eventually using injection drugs,such as heroin (Quinn et al. 196). Adolescents who undergo trauma are linked to substance abuse(Briere et al.; Dube et al.; Felitti et al.; Huang et al.; Khoury et al.; Kilpatrick et al.; Widom et al., qtd inQuinn et al. 191). They are writing to health care professionals who specialize in young children andadolescent development, physiatrists and psychologists with the interest of solving the issue beforedrug use could occur (Quinn et al. 197). These professionals all possess the ability to better identify,asses and treat said trauma with addiction and trauma receiving equal attention and merit (Quinn et al.196).The articles discussed above both attribute the root causes and the conceivable reasoning that hascreated a widespread emergency. The personal, behavioural and genetic factors that Dasgupta et al.state is backed by the article written by Quinn et al. which provides a multitude of in-depth examples ofthe ‘why’ childhood trauma occurs—which can lead to misuse of opioid analgesics and the potentialthreats of injection drug use and or overdose. Both sources address the commonly accepted notion thatthe Opioid Crisis is solely caused by medical professionals over-prescribing; both sources recommendintervention and use of introduction preventative treatment (Quinn et al. 190, Dasgupta et al. 184).Quinn et al. thoroughly examine many possible subsiding components that can lead to opioid drug use.The evidence and ‘hard facts’ ranging from age, race, gender and even geographical location clearlyspotlight just how problematic and feasible trauma is in affecting the outcomes of one’s life. My goal ofdetermining whether or not depression can be linked to the Opioid Crisis is supported by theinformation provided in this article. Depression, a possible biproduct of trauma, can demonstratestunted maturity and resilience as a result of not properly developing coping mechanisms (Quinn et al.196). This source is full of information and scientific jargon but maintains a level of compassion shownthroughout that displays sensitivity to the epidemic and a strong desire to fix the problem. I aim todemonstrate the same level of empathy in my final essay. Dasgupta et al. affirms that “…chronic painwas big business” (182). The frequency of chronic pain rising, it is intuitive how opioid analgesics wereoverabundantly introduced to those already suffering (Dasgupta et al. 182). Under the ‘Root Causes’section of the article Quinn et al. are cited, “[a]dverse childhood experiences have been strongly linkedto subsequent substance use; likewise, childhood trauma, is associated with increased use in yearslater” (Quinn et al. qtd in Dasgupta et al. 184). Each article attempts to capture the attention of thoseprescribing and treating people who could be susceptible to addition from trauma or mental illness,such as depression. The author’s backgrounds in health sciences and medicine add credibility to theinformation and potential solutions provided; their expertise reinforces my research question.Annotating and paraphrasing text from a source helped further my understanding and influenced whatside of this discussion I support, which facilitated the development of my argument. Combiningpersonal opinion and the information obtained from a source better contribute to the ongoingconversations surrounding a topic. It is important to recognize the need to properly paraphrase asource to concisely convey the intended message into your own words. When re-working content froma source, it is crucial to cite accurately; even if the wording and structure have change, that informationis not your own. By authors citing each other’s papers and opinion it gives some insight of theirmethods of reasoning, adds commentary on what other writers had to say and how it may have inspiredthem to speak about the topic.1207 wordsWORK CITEDDasgupta, Nabarun, Beletsky, Leo, Ciccarone, Daniel. Opioid Crisis: No Easy Fix to Its Socialand Economic Determinants. The American Journal of Public Health. 2018, 108; pp 182 186. EBSCO,https://eds-a-ebscohost-com.ezproxy.cotr.bc.ca/eds/pdfviewer/pdfviewer?vid=8&sid;=a0f8188b-4827-42ee-b64a-f3526665121d%40sdc-v-sessmgr03.Quinn, K, Boone L, Scheidell JD, et al. The relationships of childhood trauma and adulthoodprescription pain reliever misuse and injection drug use. Drug and Alcohol Dependence. 2016, 169; pp190-198. Science Direct,https://www.sciencedirect.com/science/article/pii/S0376871616309280.', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/Brynn Rudyk; Research Conversation; ENGL 100_2024-04-05-20-42-43/Brynn_Rudyk;_Research_Conversation;_ENGL_100_2024-04-05-20-42-43.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:43:07'),
(7, '(anonymous)', '(anonymous)', 'Ravneet Kaur BrarCaley EhnesENG100-0824 October, 2018Enigma of Widowhood and DivorceThis research conversation will address the following question: what are the psychological and socialaspects which a widow and divorcee suffer? The reason I chose this topic is that I want to represent thesituation of divorcees and widows as I have observed. The condition of divorces and widows is farbetter in developed countries than that of developing countries. In developing countries, widowhoodand divorce are considered dreadful. However, it is very difficult for a woman to survive withoutemotional support. Sometimes, women are not educated and cannot financially survive on their own.The articles, “Psychological Aspects of Widowhood and Divorce”(2009), written by J.K. Trivedi, SareenHimanshu and Dhyani Mohan and “Gender Differences in the Depressive Effect of Widowhood in LaterLife” (2001), written by R.Lee Gary, DeMaris Alfred, Stefoni Bavin and Rachel Sullivan explain that thesituations of women who are separated from their partner because of death or divorce are almost thesame since they both suffer from emotional and physical breakdown; However, the reasons for theirsituations are very different. Society treats such women very differently from that of couples who areable to remarry. This research essay analyzes the above articles and explain the relationship betweenthe two. I will also show the connection, important for citation and how to avoid plagiarism.In the essay “Psychological Aspects of Widowhood and Divorce,” (2009), J.K. Trivedi et al. contend thatwidowhood and divorce are fundamentally upsetting occasions in life (n.p.). The number of widows isgrowing as a direct result of HIV/AIDS and spousal fights and, as a result, widows often experience“poor nutrition, inadequate shelter lack of access to health care and vulnerability to violence”, (n.p.).Trivedi et al. support their claim by arguing that women work more in the family and take a biggerresponsibility for the marriage; hence, they are emotionally and physically unprepared to cope with theloss (n.p.). In addition, the authors use the example of Vrindavan, the district of Uttar Pradesh, where ayoung widow was compelled to prostitute, and a more established widow was left to ask and beg(Bruce and Damon qtd. In Trivedi et al). This example proves that how miserable is the condition ofwomen. Trivedi et al.’s purpose is to make women aware about their rights, in order to motivate womento work and enhance their social networks which will be helpful for them to gain self-confidence ratherthan being dependent (n.p.). Given the fact that this article was published by a journal of medicine,mental health, mind and their matrix, Trivedi et al. are writing to an audience of social workers andcommunity service groups. The purpose of this article is to make the audience aware of what ishappening in society in order to encourage them to support women in the best manner.In the essay “Gender Differences in the Depressive Effect of Widowhood in Later Life” (2001) GaryR.Lee, Alfred DeMaris, Stefoni Bavin, and Rachel Sullivan examine how widowhood negatively impactsthe mental state in both genders but particularly in men. They are providing six reasons about first twofactors are statistical and the other four are related to traditional gender roles (S56). Lee et al. supporttheir claim by reviewing studies about the results of differences in all the factors in order to learn howmarried and widowed people varied in “depressive symptomatology and its hypothesized antecedents”(S58). These results show that widowhood had dissimilar consequences for men and women. Inaddition, the author explains that men do get emotional support more than women from their spouseand family, but widowhood strongly affects men especially in older age. This is true in the beginning ofwidowhood of their separation as men are more affected than women because men’s local work,chores and social tasks increase but because of no interaction and experience which leads them todepression and psychological illness (S57). Lee et al. conclude by showing the result of study that“widowhood increased depressive symptomology by 4.29 points more for men than for women” (S59).Lee et al.’s. purpose was to explain and examine how men are facing more psychological andloneliness problems by analyzing depression scores on the CES-D across all models in order to betterunderstand the side effects of misery in divorce (S57). Given the fact that this was published in ajournal of gerontology, Lee et al. are writing to an audience of professionals and policy makers so thatthese people can help those who are suffering and guide to follow the right track.The article written by Trivedi et al. cites Lee as evidence to support their research regarding the real-lifeproblems of men and women after divorce or widowhood. Trivedi et al. asserts that widowhood not onlyincreases loneliness, but also social, financial, and psychological problems which lead to depression.Lee supports Trivedi’s et al. argument through Lee’s research that which gender faces morepsychological problems after widowhood. The similarity between both articles is the argument that mendo not face financial problems and neither do they become primary care takers of their children. Theyagree that sexes can suffer from psychological depression, and loneliness. These illnesses occur forthe women according to their lifestyle changes.In my final paper, I will argue that women are more affected by widowhood as compared to men. Inmany countries, cultures or the customs, the women are not allowed to re-marry; whereas, this beliefdoes not apply to men. Men easily re-marry again without any problem as there is no as such customwhich binds the men to not re-marry. For my point of view, the custom should not force womenbecause women are dependent on men both financially and emotionally, but this is not the case formen. This scenario is mostly the same in the case of divorced women as well. These sources willsupport my final paper because it prove the number of widows are increasing and adult women arefacing HIV/Aids and the treatment of such disease is very expensive. Lack of education is also anotherissue as the women cannot support themselves and their children after the death of their spouse. Thestatistics clearly show that the suffering of women is significantly more than men as women areconfined to by place and social restrictions.Citations can be helpful in avoiding plagiarism because it proves that I am able to understand whatauthor is trying to prove in his article and to summarize their ideas in my own words and other reason ithelps in doing further research. Based on class discussions and our textbook we need to keep a fewsteps in mind which includes the general topic, brainstorming, freewriting, and map making and otherpeople’s perspectives. In this article this research conversation demands citation and proper indirectquotation if we are paraphrasing any quote or research practice in academia.Work CitedTrivedi, J. K., Himanshu Sareen, and Mohan Dhyani. \"Psychological Aspects of Widowhood andDivorce.\" Mens Sana Monographs, vol. 7, no. 1, 2009, p. 37. Google Scholar, doi:10.4103/0973-1229.40648Lee, Gary R., Alfred DeMaris, Stefoni Bavin, Rachel Sullivan \"Gender Differences in the DepressiveEffect of Widowhood in Later Life.\" The Journals of Gerontology Series B: Psychological Sciences andSocial Sciences, vol. 56, no. 1, 2001, pp. S56-S61. Google Scholar, doi: org/10.1093/geronb/56.1.S56', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/Conversation (7)_2024-04-05-20-45-27/Conversation_(7)_2024-04-05-20-45-27.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:45:28'),
(8, '(anonymous)', '(anonymous)', 'Prince ThakurMs. Caley EhnesEnglish 100October 23,2018Government Surveillance vs Privacy: Who is watching you?Terrorism is of the most significant issue in the world. A lot of terrorist attacks are happening everyyear. The writing question is about how the government uses surveillance cameras to prevent an act ofterrorisms in the country. The government has access to our private information and has access towhat we do on the internet. Although some people find it disturbing that other people have access totheir personal information, this is what helps the country from experiencing terrorist attacks. The articles“INTERPOL Surveillance Network in Curbing Transnational Terrorism” By Javier Gardezabal & ToddSandler and “Who adapts MIND/FIND in INTERPOL’s fight against international crime and terrorism”By Walter Enders and Todd Sandler both explains the how the government surveillance works and howimportant it is in stopping any threats or acts of terrorism.In this conversation assignment, a writing question is chosen. After choosing the writing question, ashort and brief introduction was written. Then I provided precis for each of the article listed in theintroduction. After that, briefly described the connection between the two articles. Lastly, I reflected onthe importance of citation, and I put the work cited page at the end of the conversation assignment.The paper “INTERPOL\'S Surveillance Network in Curbing Transnational Terrorism” by JavierGardezabbal and Todd Sandler talks about how terrorist attacks are prevented with the help of theInternational Criminal Police Organization (INTERPOL), Mobile INTERPOL Network Database (MIND)and Fixed INTERPOL Network Database (FIND). The technology we have today allows police to checkevery person\'s background information and vehicle information. There are terrorists or people who stealothers travel documents, so they can travel abroad, however, MIND and FIND allows the governmentto identify the people who stole the documents. With the creation of MIND and FIND, the number ofterrorist attacks has decreased. “Therefore, the country like France that has a population of more than64 million people in 2008 could have 0.32 less transnational terrorist attacks per year, knowing theyused the INTERPOL surveillance. This then amounts to an average reduction of 30% proportionally”This article was written specifically for people in the government. Reading this paper would give peoplein the government an idea on what they should do to help prevent terrorist attacks. They will be moreaware of what steps and precautions they should do. Moreover, if the country is reading this has notadopted yet to the MIND/FIND, this will help them to decide why adapting MIND/FIND can help theircountry fight against terrorist attacks.The article “Who adopts MIND/FIND in Interpol\'s Fight against international crime and terrorism” byTodd & Sandler talks about the Mobile INTERPOL Network Database (MIND) and Fixed INTERPOLnetwork Database (FIND) technology. MIND and FIND can be used to check a person’s backgroundinformation and vehicles in the borderlines. This article is all about the different factors that influence acountry to adopt the MIND and FIND technology. MIND/FIND helps different countries to prevent anyterrorist attacks that can happen. Although MIND/FIND is very useful, still a lot of INTERPOL countrieshas not adapted this technology. They still use their ways of detecting terrorism and satisfied with justusing the help of INTERPOL. Some factors affect the decision of countries to adopt the MIND/FINDtechnology. Things such as “democratic freedom, anticipated searches for suspects, income per capitaand population” are some of the main factors that make question country if they should adaptMIND/FIND. Not all countries that use MIND/FIND technology always use it if they do, their searchesare low. MIND/FIND technology countries with a high population which is helpful to monitor everyperson considering the number of people in the country.This research paper is made for government officials in the different countries to see what are thefactors that help the countries in installing the MIND/FIND technology. It would give them a clear ideaon why they should install MIND/FIND and why other countries find it helpful to prevent terrorist attacks.This article is also open for other people to read for this would give them knowledge and be aware ofwhat is happening in the world.Overall, both essays explain to us how government surveillance works. The first essay gives us theknowledge on how helpful INTERPOL, MIND and FIND in preventing having terrorist attacks. While thesecond essay supports the first essay by about the essential thing that makes countries adopt theMIND/FIND technology in helping prevent terrorist attacks. The author of the first article used cited thesecond article several times. The first article used the second article as a support article. The secondarticle supports the ideas written in the first article.This conversation assignment has helped me to see some articles that I can use for my researchpaper. The two articles I have used in this conversation assignment has helped me to understand mytopic for the essay. I can cite from these articles. I have learned many things about the surveillancepolicies of the government in different countries how the government keeps checking on what peopleare doing in the country. I understand how advanced technologies like MIND and FIND help police andother forces to find out the suspect by using the databases. These all resources give me a clearunderstanding of how government use technology to prevent terror attacks and different problems inthe nation.Writing this conversation assignment is not easy. I had to research a lot of articles for this assignment. Ialso used a lot of time, effort and hard work to complete this work. If someone will use my assignmentwithout my permission, it is kind of disrespectful to do that. I now understand why putting citations isessential. Every article we researched has been written by other people too, and they also put the effortthe articles they have written. To use their work without their permission and without acknowledgingthem is very wrong.Word count: 999 words, excluding works cited.', '/Users/user/insideout_ms/microservice/docanalysis_service/app/uploads/uploads_save/2/Conversation Assignment (Prince T)_2024-04-05-20-48-25/Conversation_Assignment_(Prince_T)_2024-04-05-20-48-25.docx', '', 1, 1, 1, 1, 2, '2024-04-06 08:48:25');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `document_analyses`
--

CREATE TABLE `document_analyses` (
  `id` int(11) NOT NULL,
  `analysis_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `analysis_date` datetime NOT NULL DEFAULT current_timestamp(),
  `user_id` int(11) NOT NULL,
  `title` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `author` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creator` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `producer` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `keywords` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `format` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creation_date` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mod_date` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `encryption` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trapped` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pages` int(11) DEFAULT NULL,
  `language` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `success` tinyint(1) DEFAULT 1,
  `total_paragraphs` int(11) DEFAULT NULL,
  `human_count` int(11) DEFAULT NULL,
  `ai_count` int(11) DEFAULT NULL,
  `average_confidence` float DEFAULT NULL,
  `preview_success` tinyint(1) DEFAULT NULL,
  `preview_page_count` int(11) DEFAULT NULL,
  `full_preview_path` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `preview_dir` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `annotations` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`annotations`)),
  `images` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`images`)),
  `urls` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`urls`)),
  `preview_page_files` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`preview_page_files`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `document_analyses`
--

INSERT INTO `document_analyses` (`id`, `analysis_id`, `analysis_date`, `user_id`, `title`, `author`, `creator`, `producer`, `subject`, `keywords`, `format`, `creation_date`, `mod_date`, `encryption`, `trapped`, `pages`, `language`, `success`, `total_paragraphs`, `human_count`, `ai_count`, `average_confidence`, `preview_success`, `preview_page_count`, `full_preview_path`, `preview_dir`, `annotations`, `images`, `urls`, `preview_page_files`) VALUES
(1, '011383da-f370-425e-a58e-04d8318f6a60', '2025-06-13 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, 1, 0, '/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/previews/full_preview.webp', '/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/previews/pages', '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-13-15-34-33/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', '[]'),
(2, 'c3887bc6-b7c4-4dfb-8933-80cb3f467322', '2025-06-15 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, 1, 0, '/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/previews/full_preview.webp', '/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/previews/pages', '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-15-21-25-42/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', '[]'),
(3, '885f0c5a-ad9b-49eb-8989-0c0c8300d83b', '2025-06-22 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-20-04/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(4, '458e37c1-3d16-41bb-b9b7-8fb4f2bbdc1b', '2025-06-22 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-40-38/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(5, '7fe2ab92-ef72-4321-ba27-dedf88c2a2b4', '2025-06-22 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-46-24/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(6, '118826f6-d999-44e2-9d21-f97449a35fb7', '2025-06-22 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-02-55-43/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(7, 'ed4aeb66-5c35-41cc-b72a-f94db861c285', '2025-06-22 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-22-03-01-24/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(8, 'ac3ad8b3-9399-4351-b9fe-894f5bcce2db', '2025-06-22 00:00:00', 1, '(anonymous)', '(anonymous)', '(unspecified)', 'ReportLab PDF Library - www.reportlab.com', '(unspecified)', '', 'PDF 1.4', 'D:20250622031753-04\'00\'', 'D:20250622031753-04\'00\'', NULL, '', 2, 'en', 1, 40, 17, 23, 78.6996, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(9, 'b2bb3f82-b2c8-46e4-83f0-639ba33d95a5', '2025-06-23 00:00:00', 1, 'Untitled document', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 2, 'en', 1, 6, 1, 5, 63.656, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(10, 'bb5b45da-4192-4597-801c-07ef26415758', '2025-06-23 00:00:00', 1, 'Untitled document', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 2, 'en', 1, 6, 1, 5, 63.656, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(11, 'b5b4368d-1d2c-4f32-9d76-fee19375aad5', '2025-06-23 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-14-06-01/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(12, 'e8a92a7c-2a5b-4b81-b252-2eaf3ec382e4', '2025-06-23 00:00:00', 1, 'Untitled document', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 2, 'en', 1, 6, 1, 5, 63.656, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(13, '0f47b067-e033-4de1-9f1d-cd3021480e88', '2025-06-23 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-15-52/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(14, 'cbe5918c-f01d-45e3-98df-e9a9c221a7cb', '2025-06-23 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-16-30-30/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(15, '08c2ae2d-90f7-4584-9b5e-20c897586e58', '2025-06-23 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-22-03-35/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(16, '8cad1d41-98be-461e-9864-645902b6955c', '2025-06-23 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-23-23-44-00/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(17, '9b6c144b-4652-4ff3-83d4-1d394ab7ad40', '2025-06-24 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-12-24-49/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(18, '7936f838-793e-4d44-ab72-82cebce6e216', '2025-06-24 00:00:00', 1, '(anonymous)', '(anonymous)', '(unspecified)', 'ReportLab PDF Library - www.reportlab.com', '(unspecified)', '', 'PDF 1.4', 'D:20250624135737-04\'00\'', 'D:20250624135737-04\'00\'', NULL, '', 2, 'en', 1, 40, 17, 23, 78.6996, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(19, 'abdb13a0-f2e3-4a24-839c-188c1f9ab72f', '2025-06-24 00:00:00', 1, 'Untitled document', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 2, 'en', 1, 6, 1, 5, 63.656, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(20, '452ef92a-edae-4328-83f1-200c8071b925', '2025-06-24 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-14-05-49/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(21, '7259f522-d8bf-49c5-8102-2c41128f0cb5', '2025-06-24 00:00:00', 1, '(anonymous)', '(anonymous)', '(unspecified)', 'ReportLab PDF Library - www.reportlab.com', '(unspecified)', '', 'PDF 1.4', 'D:20250624145645-04\'00\'', 'D:20250624145645-04\'00\'', NULL, '', 2, 'en', 1, 40, 17, 23, 78.6996, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(22, 'b2ab15aa-9b6b-4c8d-9ee1-c69c05f048a2', '2025-06-24 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-24-15-33-45/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(23, '47575483-666c-471b-9074-d6d1504a8249', '2025-06-25 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-16-52-10/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(24, '898bea33-438e-4385-aabc-3992be58c7ac', '2025-06-25 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-06-25-20-52-08/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(25, 'a7c51044-52ce-4ce4-b204-21bd344803d5', '2025-06-25 00:00:00', 1, '(anonymous)', '(anonymous)', '(unspecified)', 'ReportLab PDF Library - www.reportlab.com', '(unspecified)', '', 'PDF 1.4', 'D:20250625225517-04\'00\'', 'D:20250625225517-04\'00\'', NULL, '', 2, 'en', 1, 40, 17, 23, 78.6996, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL),
(26, 'a182c8db-a383-4bc1-9ec8-7d35c6ba054d', '2025-07-07 00:00:00', 1, 'Fractal-ANS: A Hybrid Fractal and Asymmetric Numeral Systems Approach for High-Performance Data Compression', '', '', 'Skia/PDF m135 Google Docs Renderer', '', '', 'PDF 1.4', '', '', NULL, '', 8, 'en', 1, 43, 30, 13, 76.1732, NULL, NULL, NULL, NULL, '[]', '[\"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_3_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_3_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_4_image_number1.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_4_image_number2.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_4_image_number3.png\", \"/Users/user/Documents/xplagiax/xplagiax_cli/modules/docanalysis_service/uploads/uploads_analysis/1/Fratal_2025-07-07-21-53-42/images/image_page_5_image_number1.png\"]', '[\"https://github.com/fractal-ans/core\"]', NULL),
(27, 'b5e151b5-4802-4879-8eb6-f025146c8790', '2025-07-07 00:00:00', 1, '(anonymous)', '(anonymous)', '(unspecified)', 'ReportLab PDF Library - www.reportlab.com', '(unspecified)', '', 'PDF 1.4', 'D:20250707215711-04\'00\'', 'D:20250707215711-04\'00\'', NULL, '', 2, 'en', 1, 14, 5, 9, 81.2287, NULL, NULL, NULL, NULL, '[]', '[]', '[]', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `document_versions`
--

CREATE TABLE `document_versions` (
  `id` int(11) NOT NULL,
  `submission_id` int(11) NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `file_size` int(11) NOT NULL,
  `uploaded_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Versiones anteriores de documentos';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ErrorLogAdmin`
--

CREATE TABLE `ErrorLogAdmin` (
  `id` int(11) NOT NULL,
  `error_text` varchar(255) NOT NULL,
  `error_line` varchar(50) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ErrorLogUsers`
--

CREATE TABLE `ErrorLogUsers` (
  `id` int(11) NOT NULL,
  `modulo` varchar(100) NOT NULL,
  `funcion` varchar(50) NOT NULL,
  `error_text` varchar(255) NOT NULL,
  `error_line` varchar(50) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `files`
--

CREATE TABLE `files` (
  `id` int(11) NOT NULL,
  `filename` varchar(100) NOT NULL,
  `original_filename` varchar(100) NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `size` bigint(20) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `folder_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `minio_url` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `file_transfers`
--

CREATE TABLE `file_transfers` (
  `id` int(11) NOT NULL,
  `session_id` int(11) NOT NULL,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `remote_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `transfer_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_size` bigint(20) DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `started_at` datetime DEFAULT current_timestamp(),
  `completed_at` datetime DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `folders`
--

CREATE TABLE `folders` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `path` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `parent_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `is_shared` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `History_ai_analysis`
--

CREATE TABLE `History_ai_analysis` (
  `id` int(11) NOT NULL,
  `total_percent` decimal(10,0) DEFAULT NULL,
  `ai_percent` decimal(10,0) DEFAULT NULL,
  `probablyai_percent` decimal(10,0) DEFAULT NULL,
  `paragraph` int(11) DEFAULT NULL,
  `perplexity` decimal(10,0) DEFAULT NULL,
  `burstiness` decimal(10,0) DEFAULT NULL,
  `ai` decimal(10,0) DEFAULT NULL,
  `human` decimal(10,0) DEFAULT NULL,
  `writen_by` varchar(15) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `History_db_analysis`
--

CREATE TABLE `History_db_analysis` (
  `id` int(11) NOT NULL,
  `total_percent` decimal(10,0) DEFAULT NULL,
  `aproved_percent` decimal(10,0) DEFAULT NULL,
  `db_percent` decimal(10,0) DEFAULT NULL,
  `ai_percent` decimal(10,0) DEFAULT NULL,
  `web_percent` decimal(10,0) DEFAULT NULL,
  `img_percent` decimal(10,0) DEFAULT NULL,
  `paragraph` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Institution`
--

CREATE TABLE `Institution` (
  `id` int(11) NOT NULL,
  `institution` varchar(255) DEFAULT NULL,
  `institution_type` int(11) DEFAULT NULL,
  `city_id` int(11) DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Institution`
--

INSERT INTO `Institution` (`id`, `institution`, `institution_type`, `city_id`, `country_id`, `user_id`, `created_date`) VALUES
(1, 'College of the Rockies', 2, NULL, 2, NULL, '2025-07-03 00:13:02'),
(2, 'ABM College of Health and Technology', 2, 7, 2, NULL, '2025-07-03 00:13:02'),
(3, 'Academy of Applied Pharmaceutical Sciences', 4, 57, 2, NULL, '2025-07-03 00:13:02'),
(4, 'Academy of Business and Professional Training', 2, 57, 2, NULL, '2025-07-03 00:13:02'),
(5, 'Albert College', 5, 4, 2, NULL, '2025-07-03 00:13:02'),
(6, 'Alexander College', 2, 6, 2, NULL, '2025-07-03 00:13:02'),
(7, 'Ambrose University', 1, 7, 2, NULL, '2025-07-03 00:13:02'),
(8, 'Appleby College', 5, 36, 2, NULL, '2025-07-03 00:13:02'),
(9, 'BAC Training Centre Inc./BAC Masonry College', 2, 57, 2, NULL, '2025-07-03 00:13:02'),
(10, 'Branksome Hall', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(11, 'Brentwood College', 5, 28, 2, NULL, '2025-07-03 00:13:02'),
(12, 'British Columbia Institute of Technology', 4, 6, 2, NULL, '2025-07-03 00:13:02'),
(13, 'Burman University', 1, 22, 2, NULL, '2025-07-03 00:13:02'),
(14, 'Camosun College', 2, 61, 2, NULL, '2025-07-03 00:13:02'),
(15, 'Canadian Mennonite University', 1, 65, 2, NULL, '2025-07-03 00:13:02'),
(16, 'College Ahuntsic', 3, 30, 2, NULL, '2025-07-03 00:13:02'),
(17, 'Maisonneuve College', 3, 30, 2, NULL, '2025-07-03 00:13:02'),
(18, 'College of Rosemont', 3, 30, 2, NULL, '2025-07-03 00:13:02'),
(19, 'College Lionel-Groulx', 3, 47, 2, NULL, '2025-07-03 00:13:02'),
(20, 'College Montmorency', 3, 25, 2, NULL, '2025-07-03 00:13:02'),
(21, 'North Atlantic College', 2, 53, 2, NULL, '2025-07-03 00:13:02'),
(22, 'Columbia International College', 5, 16, 2, NULL, '2025-07-03 00:13:02'),
(23, 'Concordia University of Edmonton', 1, 10, 2, NULL, '2025-07-03 00:13:02'),
(24, 'Crandall University', 1, 29, 2, NULL, '2025-07-03 00:13:02'),
(25, 'Crescent School', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(26, 'Crestwood Preparatory College', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(27, 'Crofton House School', 5, 60, 2, NULL, '2025-07-03 00:13:02'),
(28, 'Douglas College', 2, 32, 2, NULL, '2025-07-03 00:13:02'),
(29, 'Elmwood School', 5, 38, 2, NULL, '2025-07-03 00:13:02'),
(30, 'Fanshawe College', 2, 27, 2, NULL, '2025-07-03 00:13:02'),
(31, 'Georgian College', 2, NULL, 2, NULL, '2025-07-03 00:13:02'),
(32, 'Greystone College', 2, 60, 2, NULL, '2025-07-03 00:13:02'),
(33, 'Havergal College', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(34, 'Herzing College', 2, 30, 2, NULL, '2025-07-03 00:13:02'),
(35, 'Hua Xia Acupuncture, Massage, Herb College of Canada', 4, 57, 2, NULL, '2025-07-03 00:13:02'),
(36, 'Hudson College', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(37, 'ILAC College', 2, 60, 2, NULL, '2025-07-03 00:13:02'),
(38, 'Kingsway College School', 5, 11, 2, NULL, '2025-07-03 00:13:02'),
(39, 'Kwantlen Polytechnic University', 1, 55, 2, NULL, '2025-07-03 00:13:02'),
(40, 'Lakefield College School', 5, 23, 2, NULL, '2025-07-03 00:13:02'),
(41, 'Langara College', 2, 60, 2, NULL, '2025-07-03 00:13:02'),
(42, 'LINKS Institute', 4, 60, 2, NULL, '2025-07-03 00:13:02'),
(43, 'Little Flower Academy', 5, 60, 2, NULL, '2025-07-03 00:13:02'),
(44, 'London Central Secondary School', 5, 27, 2, NULL, '2025-07-03 00:13:02'),
(45, 'M College of Canada', 2, 57, 2, NULL, '2025-07-03 00:13:02'),
(46, 'Owen Public School', 6, NULL, 2, NULL, '2025-07-03 00:13:02'),
(47, 'Pickering College', 5, 33, 2, NULL, '2025-07-03 00:13:02'),
(48, 'Prestige School - Toronto Campus', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(49, 'Quest University Canada', 1, 51, 2, NULL, '2025-07-03 00:13:02'),
(50, 'Redeemer University', 1, 1, 2, NULL, '2025-07-03 00:13:02'),
(51, 'Richard Robinson Academy of Fashion Design', 4, 38, 2, NULL, '2025-07-03 00:13:02'),
(52, 'Rose Avenue Junior Public School', 6, 57, 2, NULL, '2025-07-03 00:13:02'),
(53, 'Rundle College', 5, 7, 2, NULL, '2025-07-03 00:13:02'),
(54, 'Southridge School', 5, 55, 2, NULL, '2025-07-03 00:13:02'),
(55, 'St. George\'s School', 5, 60, 2, NULL, '2025-07-03 00:13:02'),
(56, 'St. Mary\'s University', 1, 7, 2, NULL, '2025-07-03 00:13:02'),
(57, 'St. Michael\'s Choir School', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(58, 'The Bishop Strachan School', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(59, 'The York School', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(60, 'Trebas Institute', 4, 30, 2, NULL, '2025-07-03 00:13:02'),
(61, 'Université de Hearst', 1, 17, 2, NULL, '2025-07-03 00:13:02'),
(62, 'Université de King\'s College', 1, 15, 2, NULL, '2025-07-03 00:13:02'),
(63, 'Université de l\'Île-du-Prince-Édouard', 1, 8, 2, NULL, '2025-07-03 00:13:02'),
(64, 'Université de l\'Ontario français', 1, 57, 2, NULL, '2025-07-03 00:13:02'),
(65, 'Université de Moncton', 1, 29, 2, NULL, '2025-07-03 00:13:02'),
(66, 'Université de NSCAD', 1, 15, 2, NULL, '2025-07-03 00:13:02'),
(67, 'Université de Saint-Boniface', 1, 65, 2, NULL, '2025-07-03 00:13:02'),
(68, 'Université de Saint-Michel', 1, 57, 2, NULL, '2025-07-03 00:13:02'),
(69, 'Université de Saint-Paul', 1, 38, 2, NULL, '2025-07-03 00:13:02'),
(70, 'Université de Sudbury', 1, 54, 2, NULL, '2025-07-03 00:13:02'),
(71, 'Université de Trinity College', 1, 57, 2, NULL, '2025-07-03 00:13:02'),
(72, 'Université du Québec', 1, 41, 2, NULL, '2025-07-03 00:13:02'),
(73, 'Université du Québec à Chicoutimi (UQAC)', 1, 9, 2, NULL, '2025-07-03 00:13:02'),
(74, 'Université du Québec à Rimouski (UQAR)', 1, 43, 2, NULL, '2025-07-03 00:13:02'),
(75, 'Université du Québec à Trois-Rivières (UQTR)', 1, 58, 2, NULL, '2025-07-03 00:13:02'),
(76, 'Université du Québec en Abitibi-Témiscamingue (UQAT)', 1, 44, 2, NULL, '2025-07-03 00:13:02'),
(77, 'Université du Québec en Outaouais (UQO)', 1, 13, 2, NULL, '2025-07-03 00:13:02'),
(78, 'Université Sainte-Anne', 1, NULL, 2, NULL, '2025-07-03 00:13:02'),
(79, 'Université TÉLUQ', 1, 41, 2, NULL, '2025-07-03 00:13:02'),
(80, 'University Canada West', 1, 60, 2, NULL, '2025-07-03 00:13:02'),
(81, 'University of King\'s College', 1, 15, 2, NULL, '2025-07-03 00:13:02'),
(82, 'University of Ontario Institute of Technology', 1, 37, 2, NULL, '2025-07-03 00:13:02'),
(83, 'Upper Canada College', 5, 57, 2, NULL, '2025-07-03 00:13:02'),
(84, 'Vancouver Island University', 1, 31, 2, NULL, '2025-07-03 00:13:02'),
(85, 'W. Erskine Johnston Public School', 6, 19, 2, NULL, '2025-07-03 00:13:02'),
(86, 'West Point Grey Academy', 5, 60, 2, NULL, '2025-07-03 00:13:02'),
(87, 'York House School', 5, 60, 2, NULL, '2025-07-03 00:13:02'),
(88, 'Yorkville University', 1, 57, 2, NULL, '2025-07-03 00:13:02'),
(89, 'Yukon University', 1, 63, 2, NULL, '2025-07-03 00:13:02'),
(90, 'Southern Alberta Institute of Technology', 4, 7, 2, NULL, '2025-07-03 00:13:02'),
(91, 'Simon Fraser University (SFU)', 1, 6, 2, NULL, '2025-07-03 00:13:02'),
(92, 'University of British Columbia (UBC)', 1, 60, 2, NULL, '2025-07-03 00:13:02'),
(93, 'Thompson Rivers University (TRU)', 1, 18, 2, NULL, '2025-07-03 00:13:02'),
(94, 'University of New Brunswick (UNB)', 1, 12, 2, NULL, '2025-07-03 00:13:02'),
(95, 'University of Western Ontario (Western)', 1, 27, 2, NULL, '2025-07-03 00:13:02');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Institution_type`
--

CREATE TABLE `Institution_type` (
  `id` int(11) NOT NULL,
  `institution_type` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Institution_type`
--

INSERT INTO `Institution_type` (`id`, `institution_type`, `user_id`, `created_date`) VALUES
(1, 'University', NULL, '2025-06-03 19:04:19'),
(2, 'College', NULL, '2025-06-03 19:04:19'),
(3, 'Cégep', NULL, '2025-06-03 19:04:19'),
(4, 'Technical Institute', NULL, '2025-06-03 19:04:19'),
(5, 'High School', NULL, '2025-06-03 19:04:19'),
(6, 'Elementary School', NULL, '2025-06-03 19:04:19');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Lenguage`
--

CREATE TABLE `Lenguage` (
  `id` int(11) NOT NULL,
  `lenguage_name` varchar(50) DEFAULT NULL,
  `lenguage` varchar(2) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Lenguage`
--

INSERT INTO `Lenguage` (`id`, `lenguage_name`, `lenguage`, `user_id`, `created_date`) VALUES
(1, 'English', 'en', NULL, '2024-02-19 20:06:42'),
(2, 'Spanish', 'es', NULL, '2024-02-19 20:06:42'),
(13, 'Frances', 'fr', NULL, '2025-07-01 22:13:13'),
(14, 'Aleman', 'de', NULL, '2025-07-01 23:22:05');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `log_status`
--

CREATE TABLE `log_status` (
  `id` int(11) NOT NULL,
  `status` varchar(10) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `log_status`
--

INSERT INTO `log_status` (`id`, `status`, `created_date`) VALUES
(1, 'Loguin', '2024-02-19 19:57:42'),
(2, 'logout', '2024-02-19 19:57:42');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Patents`
--

CREATE TABLE `Patents` (
  `id` int(11) NOT NULL,
  `WKU` varchar(25) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `App_Date` varchar(14) DEFAULT NULL,
  `Issue_Date` varchar(14) DEFAULT NULL,
  `Inventor` varchar(255) DEFAULT NULL,
  `Assignee` varchar(100) DEFAULT NULL,
  `ICL_Class` varchar(100) DEFAULT NULL,
  `Reference` varchar(100) DEFAULT NULL,
  `Claims` longtext DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `Province_state`
--

CREATE TABLE `Province_state` (
  `id` int(11) NOT NULL,
  `province_state` varchar(255) DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `Province_state`
--

INSERT INTO `Province_state` (`id`, `province_state`, `country_id`, `user_id`, `created_date`) VALUES
(1, 'Alberta', 2, NULL, '2025-06-03 18:36:38'),
(2, 'British Columbia', 2, NULL, '2025-06-03 18:36:38'),
(3, 'Prince Edward Island', 2, NULL, '2025-06-03 18:36:38'),
(4, 'Manitoba', 2, NULL, '2025-06-03 18:36:38'),
(5, 'Nova Scotia', 2, NULL, '2025-06-03 18:36:38'),
(6, 'New Brunswick', 2, NULL, '2025-06-03 18:36:38'),
(7, 'Ontario', 2, NULL, '2025-06-03 18:36:38'),
(8, 'Quebec', 2, NULL, '2025-06-03 18:36:38'),
(9, 'Saskatchewan', 2, NULL, '2025-06-03 18:36:38'),
(10, 'Newfoundland and Labrador', 2, NULL, '2025-06-03 18:36:38'),
(11, 'Yukon', 2, NULL, '2025-06-03 18:36:38');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `services`
--

CREATE TABLE `services` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `display_name` varchar(200) NOT NULL,
  `host` varchar(255) NOT NULL,
  `port` int(11) NOT NULL,
  `service_type` varchar(50) NOT NULL,
  `endpoint` varchar(500) DEFAULT NULL,
  `timeout` int(11) DEFAULT 5,
  `icon` varchar(100) DEFAULT 'fas fa-server',
  `username` varchar(100) DEFAULT NULL,
  `password_encrypted` text DEFAULT NULL,
  `extra_config` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_monitored` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `services`
--

INSERT INTO `services` (`id`, `name`, `display_name`, `host`, `port`, `service_type`, `endpoint`, `timeout`, `icon`, `username`, `password_encrypted`, `extra_config`, `is_active`, `is_monitored`, `created_at`, `updated_at`, `created_by`) VALUES
(1, 'elasticsearch', 'Elasticsearch', 'localhost', 9200, 'http', '/_cluster/health', 5, 'fas fa-search', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(2, 'clamav', 'ClamAV', 'localhost', 3310, 'socket', NULL, 5, 'fas fa-shield-virus', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(3, 'redis', 'Redis', 'localhost', 6379, 'redis', NULL, 5, 'fas fa-database', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(4, 'mysql', 'MySQL', 'localhost', 3306, 'mysql', NULL, 5, 'fas fa-server', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(5, 'qdrant', 'Qdrant', 'localhost', 6333, 'http', '/health', 5, 'fas fa-vector-square', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(6, 'minio', 'MinIO', 'localhost', 9500, 'http', '/minio/health/live', 5, 'fas fa-cloud', NULL, NULL, NULL, 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL),
(7, 'rabbitmq', 'RabbitMQ', 'localhost', 5672, 'rabbitmq', NULL, 5, 'fas fa-exchange-alt', NULL, NULL, '{\"management_port\": 15672}', 1, 1, '2025-07-07 10:50:30', '2025-07-07 10:50:30', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `service_logs`
--

CREATE TABLE `service_logs` (
  `id` int(11) NOT NULL,
  `service_id` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL,
  `response_time` double DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `additional_data` text DEFAULT NULL,
  `checked_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `service_logs`
--

INSERT INTO `service_logs` (`id`, `service_id`, `status`, `response_time`, `error_message`, `additional_data`, `checked_at`) VALUES
(1, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10753c210>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:21:16'),
(2, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10754f1d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:21:19'),
(3, 4, 1, 0.003042936325073242, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 2523, \"connections\": 2}', '2025-07-07 15:21:24'),
(4, 7, 0, 0.014457941055297852, '', NULL, '2025-07-07 15:21:26'),
(5, 3, 1, 0.006119966506958008, NULL, '{\"version\": \"7.4.2\", \"uptime\": 333, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:21:31'),
(6, 5, 0, 0.010083, NULL, NULL, '2025-07-07 15:21:33'),
(7, 5, 0, 0.008781, NULL, NULL, '2025-07-07 15:21:35'),
(8, 1, 1, 0.015, NULL, NULL, '2025-07-07 15:21:38'),
(9, 2, 1, 0.0005018711090087891, NULL, NULL, '2025-07-07 15:21:39'),
(10, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x1074f77d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:21:42'),
(11, 4, 1, 0.006680965423583984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 2542, \"connections\": 2}', '2025-07-07 15:21:43'),
(12, 3, 1, 0.006281852722167969, NULL, '{\"version\": \"7.4.2\", \"uptime\": 348, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:21:46'),
(13, 7, 0, 0.016782760620117188, '', NULL, '2025-07-07 15:21:49'),
(14, 4, 1, 0.0037970542907714844, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 2551, \"connections\": 2}', '2025-07-07 15:21:52'),
(15, 4, 1, 0.0026476383209228516, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 2553, \"connections\": 2}', '2025-07-07 15:21:54'),
(16, 2, 1, 0.0005931854248046875, NULL, NULL, '2025-07-07 15:21:59'),
(17, 1, 1, 0.011869, NULL, NULL, '2025-07-07 15:22:00'),
(18, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x1073f3f90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:22:02'),
(19, 5, 0, 0.004439, NULL, NULL, '2025-07-07 15:22:03'),
(20, 2, 1, 0.0005221366882324219, NULL, NULL, '2025-07-07 15:30:35'),
(21, 2, 1, 0.0006191730499267578, NULL, NULL, '2025-07-07 15:30:41'),
(22, 1, 1, 0.01581, NULL, NULL, '2025-07-07 15:30:47'),
(23, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10756f510>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:30:49'),
(24, 4, 1, 0.0026090145111083984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 3090, \"connections\": 2}', '2025-07-07 15:30:51'),
(25, 2, 1, 0.000637054443359375, NULL, NULL, '2025-07-07 15:36:01'),
(26, 1, 1, 0.016496, NULL, NULL, '2025-07-07 15:36:05'),
(27, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10751ac10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:36:06'),
(28, 4, 1, 0.0039370059967041016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 3407, \"connections\": 2}', '2025-07-07 15:36:08'),
(29, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x1075c58d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:36:10'),
(30, 3, 1, 0.006978034973144531, NULL, '{\"version\": \"7.4.2\", \"uptime\": 1214, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:36:12'),
(31, 7, 0, 0.009974002838134766, '', NULL, '2025-07-07 15:36:13'),
(32, 5, 0, 0.004653, NULL, NULL, '2025-07-07 15:36:14'),
(33, 2, 1, 0.001135110855102539, NULL, NULL, '2025-07-07 15:36:17'),
(34, 1, 1, 0.013512, NULL, NULL, '2025-07-07 15:36:18'),
(35, 1, 1, 0.012804, NULL, NULL, '2025-07-07 15:37:31'),
(36, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10756e510>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:37:32'),
(37, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:39:50'),
(38, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:39:55'),
(39, 2, 1, 0.0006000995635986328, NULL, NULL, '2025-07-07 15:40:02'),
(40, 1, 1, 0.023119, NULL, NULL, '2025-07-07 15:58:30'),
(41, 2, 1, 0.0013120174407958984, NULL, NULL, '2025-07-07 15:58:30'),
(42, 3, 1, 0.12550711631774902, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2552, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:58:30'),
(43, 4, 1, 0.008905172348022461, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4749, \"connections\": 2}', '2025-07-07 15:58:30'),
(44, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:58:30'),
(45, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f19ac10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:58:30'),
(46, 7, 0, 0.03088998794555664, '', NULL, '2025-07-07 15:58:30'),
(47, 1, 1, 0.017313, NULL, NULL, '2025-07-07 15:58:40'),
(48, 2, 1, 0.003197908401489258, NULL, NULL, '2025-07-07 15:58:40'),
(49, 3, 1, 0.01808786392211914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2562, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:58:40'),
(50, 4, 1, 0.00710606575012207, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4759, \"connections\": 2}', '2025-07-07 15:58:40'),
(51, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:58:40'),
(52, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1feb10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:58:40'),
(53, 7, 0, 0.009451150894165039, '', NULL, '2025-07-07 15:58:40'),
(54, 1, 1, 0.015378, NULL, NULL, '2025-07-07 15:58:50'),
(55, 2, 1, 0.00046896934509277344, NULL, NULL, '2025-07-07 15:58:50'),
(56, 3, 1, 0.009773015975952148, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2572, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:58:50'),
(57, 4, 1, 0.004054069519042969, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4769, \"connections\": 2}', '2025-07-07 15:58:50'),
(58, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:58:50'),
(59, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f112290>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:58:50'),
(60, 7, 0, 0.010640144348144531, '', NULL, '2025-07-07 15:58:50'),
(61, 2, 1, 0.0005040168762207031, NULL, NULL, '2025-07-07 15:58:52'),
(62, 1, 1, 0.013339, NULL, NULL, '2025-07-07 15:58:54'),
(63, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f10d550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:58:57'),
(64, 4, 1, 0.005202054977416992, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4778, \"connections\": 2}', '2025-07-07 15:58:59'),
(65, 1, 1, 0.009104, NULL, NULL, '2025-07-07 15:59:00'),
(66, 2, 1, 0.0004711151123046875, NULL, NULL, '2025-07-07 15:59:00'),
(67, 3, 1, 0.005589962005615234, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2582, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:00'),
(68, 4, 1, 0.004091739654541016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4779, \"connections\": 2}', '2025-07-07 15:59:00'),
(69, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:59:00'),
(70, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f156450>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:00'),
(71, 7, 0, 0.014794111251831055, '', NULL, '2025-07-07 15:59:00'),
(72, 3, 1, 0.007761955261230469, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2585, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:03'),
(73, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:59:09'),
(74, 1, 1, 0.008034, NULL, NULL, '2025-07-07 15:59:10'),
(75, 2, 1, 0.0010488033294677734, NULL, NULL, '2025-07-07 15:59:10'),
(76, 3, 1, 0.0064198970794677734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2592, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:10'),
(77, 4, 1, 0.0027952194213867188, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4789, \"connections\": 2}', '2025-07-07 15:59:10'),
(78, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:59:10'),
(79, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f110810>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:10'),
(80, 7, 0, 0.006482839584350586, '', NULL, '2025-07-07 15:59:10'),
(81, 1, 1, 0.019385, NULL, NULL, '2025-07-07 15:59:20'),
(82, 2, 1, 0.0008640289306640625, NULL, NULL, '2025-07-07 15:59:20'),
(83, 3, 1, 0.008620023727416992, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2602, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:20'),
(84, 4, 1, 0.0027718544006347656, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4799, \"connections\": 2}', '2025-07-07 15:59:20'),
(85, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:59:20'),
(86, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f157f50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:20'),
(87, 7, 0, 0.007857084274291992, '', NULL, '2025-07-07 15:59:20'),
(88, 1, 1, 0.017061, NULL, NULL, '2025-07-07 15:59:30'),
(89, 2, 1, 0.0006620883941650391, NULL, NULL, '2025-07-07 15:59:30'),
(90, 3, 1, 0.006704807281494141, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2612, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:30'),
(91, 4, 1, 0.0031609535217285156, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4809, \"connections\": 2}', '2025-07-07 15:59:30'),
(92, 5, 0, NULL, '(\'Connection aborted.\', BadStatusLine(\'\\x00\\x00\\x12\\x04\\x00\\x00\\x00\\x00\\x00\\x00\\x04\\x00\\x10\\x00\\x00\\x00\\x05\\x00\\x00@\\x00\\x00\\x06\\x01\\x00\\x00\\x00\'))', NULL, '2025-07-07 15:59:30'),
(93, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f2006d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:30'),
(94, 7, 0, 0.008352994918823242, '', NULL, '2025-07-07 15:59:30'),
(95, 1, 1, 0.010708, NULL, NULL, '2025-07-07 15:59:45'),
(96, 2, 1, 0.0035598278045654297, NULL, NULL, '2025-07-07 15:59:45'),
(97, 3, 1, 0.012450933456420898, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2627, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:45'),
(98, 4, 1, 0.002935171127319336, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4824, \"connections\": 2}', '2025-07-07 15:59:45'),
(99, 5, 0, 0.006914, NULL, NULL, '2025-07-07 15:59:45'),
(100, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f114b50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:45'),
(101, 7, 0, 0.012604236602783203, '', NULL, '2025-07-07 15:59:45'),
(102, 1, 1, 0.032326, NULL, NULL, '2025-07-07 15:59:50'),
(103, 2, 1, 0.0018208026885986328, NULL, NULL, '2025-07-07 15:59:50'),
(104, 3, 1, 0.006265163421630859, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2632, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 15:59:50'),
(105, 4, 1, 0.004480838775634766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4829, \"connections\": 2}', '2025-07-07 15:59:50'),
(106, 5, 0, 0.0088, NULL, NULL, '2025-07-07 15:59:50'),
(107, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f116e10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 15:59:50'),
(108, 7, 0, 0.019306182861328125, '', NULL, '2025-07-07 15:59:50'),
(109, 5, 0, 0.004979, NULL, NULL, '2025-07-07 15:59:52'),
(110, 1, 1, 0.023506, NULL, NULL, '2025-07-07 16:00:16'),
(111, 2, 1, 0.001940011978149414, NULL, NULL, '2025-07-07 16:00:16'),
(112, 3, 1, 0.007155179977416992, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2658, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:00:16'),
(113, 4, 1, 0.004285335540771484, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4855, \"connections\": 2}', '2025-07-07 16:00:16'),
(114, 5, 0, 0.00517, NULL, NULL, '2025-07-07 16:00:16'),
(115, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f115e90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:00:16'),
(116, 7, 0, 0.011750221252441406, '', NULL, '2025-07-07 16:00:16'),
(117, 1, 1, 0.014563, NULL, NULL, '2025-07-07 16:00:26'),
(118, 2, 1, 0.001331329345703125, NULL, NULL, '2025-07-07 16:00:26'),
(119, 3, 1, 0.0060808658599853516, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2668, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:00:26'),
(120, 4, 1, 0.003493785858154297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4865, \"connections\": 2}', '2025-07-07 16:00:26'),
(121, 5, 0, 0.005233, NULL, NULL, '2025-07-07 16:00:26'),
(122, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f114d10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:00:26'),
(123, 7, 0, 0.006495952606201172, '', NULL, '2025-07-07 16:00:26'),
(124, 1, 1, 0.012245, NULL, NULL, '2025-07-07 16:00:36'),
(125, 2, 1, 0.0014872550964355469, NULL, NULL, '2025-07-07 16:00:36'),
(126, 3, 1, 0.00538182258605957, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2678, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:00:36'),
(127, 4, 1, 0.0029151439666748047, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4875, \"connections\": 2}', '2025-07-07 16:00:36'),
(128, 5, 0, 0.005154, NULL, NULL, '2025-07-07 16:00:36'),
(129, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f203350>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:00:36'),
(130, 7, 0, 0.008365154266357422, '', NULL, '2025-07-07 16:00:36'),
(131, 1, 1, 0.012916, NULL, NULL, '2025-07-07 16:00:46'),
(132, 2, 1, 0.0009140968322753906, NULL, NULL, '2025-07-07 16:00:46'),
(133, 3, 1, 0.009530067443847656, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2688, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:00:46'),
(134, 4, 1, 0.010406732559204102, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4885, \"connections\": 2}', '2025-07-07 16:00:46'),
(135, 5, 0, 0.004761, NULL, NULL, '2025-07-07 16:00:46'),
(136, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f156a50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:00:46'),
(137, 7, 0, 0.009398937225341797, '', NULL, '2025-07-07 16:00:46'),
(138, 1, 1, 0.022564, NULL, NULL, '2025-07-07 16:00:56'),
(139, 2, 1, 0.0005629062652587891, NULL, NULL, '2025-07-07 16:00:56'),
(140, 3, 1, 0.0070040225982666016, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2698, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:00:56'),
(141, 4, 1, 0.0073359012603759766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4895, \"connections\": 2}', '2025-07-07 16:00:56'),
(142, 5, 0, 0.005328, NULL, NULL, '2025-07-07 16:00:56'),
(143, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f156a50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:00:56'),
(144, 7, 0, 0.010579824447631836, '', NULL, '2025-07-07 16:00:56'),
(145, 1, 1, 0.016368, NULL, NULL, '2025-07-07 16:01:06'),
(146, 2, 1, 0.0008807182312011719, NULL, NULL, '2025-07-07 16:01:06'),
(147, 3, 1, 0.005860090255737305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2708, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:06'),
(148, 4, 1, 0.0032587051391601562, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4905, \"connections\": 2}', '2025-07-07 16:01:06'),
(149, 5, 0, 0.004363, NULL, NULL, '2025-07-07 16:01:06'),
(150, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f15e250>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:06'),
(151, 7, 0, 0.006487131118774414, '', NULL, '2025-07-07 16:01:06'),
(152, 1, 1, 0.014227, NULL, NULL, '2025-07-07 16:01:16'),
(153, 2, 1, 0.001439809799194336, NULL, NULL, '2025-07-07 16:01:16'),
(154, 3, 1, 0.006014108657836914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2718, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:16'),
(155, 4, 1, 0.0026988983154296875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4915, \"connections\": 2}', '2025-07-07 16:01:16'),
(156, 5, 0, 0.005667, NULL, NULL, '2025-07-07 16:01:16'),
(157, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f187cd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:16'),
(158, 7, 0, 0.006687164306640625, '', NULL, '2025-07-07 16:01:16'),
(159, 1, 1, 0.02443, NULL, NULL, '2025-07-07 16:01:26'),
(160, 2, 1, 0.0005710124969482422, NULL, NULL, '2025-07-07 16:01:26'),
(161, 3, 1, 0.011970996856689453, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2728, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:26'),
(162, 4, 1, 0.007795095443725586, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4925, \"connections\": 2}', '2025-07-07 16:01:26'),
(163, 5, 0, 0.003683, NULL, NULL, '2025-07-07 16:01:26'),
(164, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f0d7e10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:26'),
(165, 7, 0, 0.0122528076171875, '', NULL, '2025-07-07 16:01:26'),
(166, 1, 1, 0.01477, NULL, NULL, '2025-07-07 16:01:34'),
(167, 2, 1, 0.0005609989166259766, NULL, NULL, '2025-07-07 16:01:34'),
(168, 3, 1, 0.01273202896118164, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2736, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:34'),
(169, 4, 1, 0.0068171024322509766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4933, \"connections\": 2}', '2025-07-07 16:01:34'),
(170, 5, 0, 0.009769, NULL, NULL, '2025-07-07 16:01:34'),
(171, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f24a990>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:34'),
(172, 7, 0, 0.04222583770751953, '', NULL, '2025-07-07 16:01:34'),
(173, 1, 1, 0.012572, NULL, NULL, '2025-07-07 16:01:37'),
(174, 2, 1, 0.0004658699035644531, NULL, NULL, '2025-07-07 16:01:37'),
(175, 3, 1, 0.005995988845825195, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2739, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:37'),
(176, 4, 1, 0.0034592151641845703, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4936, \"connections\": 2}', '2025-07-07 16:01:37'),
(177, 5, 0, 0.004278, NULL, NULL, '2025-07-07 16:01:37'),
(178, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f23abd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:37'),
(179, 7, 0, 0.009219646453857422, '', NULL, '2025-07-07 16:01:37'),
(180, 1, 1, 0.010942, NULL, NULL, '2025-07-07 16:01:38'),
(181, 2, 1, 0.0008337497711181641, NULL, NULL, '2025-07-07 16:01:38'),
(182, 3, 1, 0.006860017776489258, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2740, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:38'),
(183, 4, 1, 0.0032918453216552734, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4937, \"connections\": 2}', '2025-07-07 16:01:38'),
(184, 5, 0, 0.004159, NULL, NULL, '2025-07-07 16:01:38'),
(185, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f239610>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:38'),
(186, 7, 0, 0.010502099990844727, '', NULL, '2025-07-07 16:01:38'),
(187, 1, 1, 0.016262, NULL, NULL, '2025-07-07 16:01:44'),
(188, 2, 1, 0.0004620552062988281, NULL, NULL, '2025-07-07 16:01:44'),
(189, 3, 1, 0.006181001663208008, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2746, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:44'),
(190, 4, 1, 0.002875804901123047, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4943, \"connections\": 2}', '2025-07-07 16:01:44'),
(191, 5, 0, 0.003946, NULL, NULL, '2025-07-07 16:01:44'),
(192, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f24aa50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:44'),
(193, 7, 0, 0.01076507568359375, '', NULL, '2025-07-07 16:01:44'),
(194, 1, 1, 0.014694, NULL, NULL, '2025-07-07 16:01:54'),
(195, 2, 1, 0.0011458396911621094, NULL, NULL, '2025-07-07 16:01:54'),
(196, 3, 1, 0.008285045623779297, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2756, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:01:54'),
(197, 4, 1, 0.004220247268676758, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4953, \"connections\": 2}', '2025-07-07 16:01:54'),
(198, 5, 0, 0.006205, NULL, NULL, '2025-07-07 16:01:54'),
(199, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f186290>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:01:54'),
(200, 7, 0, 0.015658855438232422, '', NULL, '2025-07-07 16:01:54'),
(201, 1, 1, 0.011338, NULL, NULL, '2025-07-07 16:02:04'),
(202, 2, 1, 0.0005140304565429688, NULL, NULL, '2025-07-07 16:02:04'),
(203, 3, 1, 0.00952601432800293, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2766, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:04'),
(204, 4, 1, 0.00484919548034668, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4963, \"connections\": 2}', '2025-07-07 16:02:04'),
(205, 5, 0, 0.003898, NULL, NULL, '2025-07-07 16:02:04'),
(206, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f24bb50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:04'),
(207, 7, 0, 0.011487007141113281, '', NULL, '2025-07-07 16:02:04'),
(208, 1, 1, 0.009031, NULL, NULL, '2025-07-07 16:02:14'),
(209, 2, 1, 0.0004849433898925781, NULL, NULL, '2025-07-07 16:02:14'),
(210, 3, 1, 0.00571894645690918, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2776, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:14'),
(211, 4, 1, 0.0031499862670898438, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4973, \"connections\": 2}', '2025-07-07 16:02:14'),
(212, 5, 0, 0.004367, NULL, NULL, '2025-07-07 16:02:14'),
(213, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f187550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:14'),
(214, 7, 0, 0.005296945571899414, '', NULL, '2025-07-07 16:02:14'),
(215, 1, 1, 0.067147, NULL, NULL, '2025-07-07 16:02:24'),
(216, 2, 1, 0.0014710426330566406, NULL, NULL, '2025-07-07 16:02:24'),
(217, 3, 1, 0.0074422359466552734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2786, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:24'),
(218, 4, 1, 0.004588127136230469, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4983, \"connections\": 2}', '2025-07-07 16:02:24'),
(219, 5, 0, 0.003992, NULL, NULL, '2025-07-07 16:02:24'),
(220, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f238710>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:24'),
(221, 7, 0, 0.010729074478149414, '', NULL, '2025-07-07 16:02:24'),
(222, 1, 1, 0.028651, NULL, NULL, '2025-07-07 16:02:34'),
(223, 2, 1, 0.028510093688964844, NULL, NULL, '2025-07-07 16:02:34'),
(224, 3, 1, 0.027883052825927734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2796, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:34'),
(225, 4, 1, 0.005095958709716797, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4993, \"connections\": 2}', '2025-07-07 16:02:34'),
(226, 5, 0, 0.006074, NULL, NULL, '2025-07-07 16:02:34'),
(227, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f23b950>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:34'),
(228, 7, 0, 0.03598284721374512, '', NULL, '2025-07-07 16:02:34'),
(229, 1, 1, 0.016622, NULL, NULL, '2025-07-07 16:02:44'),
(230, 2, 1, 0.0018210411071777344, NULL, NULL, '2025-07-07 16:02:44'),
(231, 3, 1, 0.008140087127685547, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2806, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:44'),
(232, 4, 1, 0.0041959285736083984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5003, \"connections\": 2}', '2025-07-07 16:02:44'),
(233, 5, 0, 0.009514, NULL, NULL, '2025-07-07 16:02:44'),
(234, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f238b50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:44'),
(235, 7, 0, 0.014774799346923828, '', NULL, '2025-07-07 16:02:44'),
(236, 1, 1, 0.024635, NULL, NULL, '2025-07-07 16:02:54'),
(237, 2, 1, 0.003545045852661133, NULL, NULL, '2025-07-07 16:02:54'),
(238, 3, 1, 0.015011072158813477, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2816, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:02:54'),
(239, 4, 1, 0.01908397674560547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5013, \"connections\": 2}', '2025-07-07 16:02:54'),
(240, 5, 0, 0.010599, NULL, NULL, '2025-07-07 16:02:54'),
(241, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f202b10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:02:54'),
(242, 7, 0, 0.015991926193237305, '', NULL, '2025-07-07 16:02:54'),
(243, 1, 1, 0.040147, NULL, NULL, '2025-07-07 16:03:04'),
(244, 2, 1, 0.0006251335144042969, NULL, NULL, '2025-07-07 16:03:04'),
(245, 3, 1, 0.0077571868896484375, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2826, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:04'),
(246, 4, 1, 0.0033349990844726562, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5023, \"connections\": 2}', '2025-07-07 16:03:04'),
(247, 5, 0, 0.003583, NULL, NULL, '2025-07-07 16:03:04'),
(248, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f23ac90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:04'),
(249, 7, 0, 0.02349686622619629, '', NULL, '2025-07-07 16:03:04'),
(250, 1, 1, 0.018583, NULL, NULL, '2025-07-07 16:03:14'),
(251, 2, 1, 0.001062154769897461, NULL, NULL, '2025-07-07 16:03:14'),
(252, 3, 1, 0.009209156036376953, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2836, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:14'),
(253, 4, 1, 0.0380549430847168, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5033, \"connections\": 2}', '2025-07-07 16:03:14'),
(254, 5, 0, 0.003958, NULL, NULL, '2025-07-07 16:03:14'),
(255, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1552d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:14'),
(256, 7, 0, 0.009057044982910156, '', NULL, '2025-07-07 16:03:14'),
(257, 1, 1, 0.051146, NULL, NULL, '2025-07-07 16:03:24'),
(258, 2, 1, 0.0006170272827148438, NULL, NULL, '2025-07-07 16:03:24'),
(259, 3, 1, 0.014953851699829102, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2846, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:24'),
(260, 4, 1, 0.0516510009765625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5043, \"connections\": 2}', '2025-07-07 16:03:24'),
(261, 5, 0, 0.005323, NULL, NULL, '2025-07-07 16:03:24'),
(262, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f203bd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:24'),
(263, 7, 0, 0.03898906707763672, '', NULL, '2025-07-07 16:03:24'),
(264, 1, 1, 0.01368, NULL, NULL, '2025-07-07 16:03:34'),
(265, 2, 1, 0.0007407665252685547, NULL, NULL, '2025-07-07 16:03:34'),
(266, 3, 1, 0.006945133209228516, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2856, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:34'),
(267, 4, 1, 0.0042858123779296875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5053, \"connections\": 2}', '2025-07-07 16:03:34'),
(268, 5, 0, 0.00788, NULL, NULL, '2025-07-07 16:03:34'),
(269, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f155d50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:34'),
(270, 7, 0, 0.015652894973754883, '', NULL, '2025-07-07 16:03:34'),
(271, 1, 1, 0.012099, NULL, NULL, '2025-07-07 16:03:44'),
(272, 2, 1, 0.0005750656127929688, NULL, NULL, '2025-07-07 16:03:44'),
(273, 3, 1, 0.008079767227172852, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2866, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:44'),
(274, 4, 1, 0.0035610198974609375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5063, \"connections\": 2}', '2025-07-07 16:03:44'),
(275, 5, 0, 0.00498, NULL, NULL, '2025-07-07 16:03:44'),
(276, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f203b10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:44'),
(277, 7, 0, 0.01659536361694336, '', NULL, '2025-07-07 16:03:44'),
(278, 1, 1, 0.017793, NULL, NULL, '2025-07-07 16:03:54'),
(279, 2, 1, 0.0026099681854248047, NULL, NULL, '2025-07-07 16:03:54'),
(280, 3, 1, 0.008372068405151367, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2876, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:03:54'),
(281, 4, 1, 0.033683061599731445, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5073, \"connections\": 2}', '2025-07-07 16:03:54'),
(282, 5, 0, 0.004819, NULL, NULL, '2025-07-07 16:03:54'),
(283, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f184e50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:03:54'),
(284, 7, 0, 0.010360240936279297, '', NULL, '2025-07-07 16:03:54'),
(285, 1, 1, 0.026363, NULL, NULL, '2025-07-07 16:04:04'),
(286, 2, 1, 0.001958131790161133, NULL, NULL, '2025-07-07 16:04:04'),
(287, 3, 1, 0.011874914169311523, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2886, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:04'),
(288, 4, 1, 0.007463932037353516, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5083, \"connections\": 2}', '2025-07-07 16:04:04'),
(289, 5, 0, 0.01116, NULL, NULL, '2025-07-07 16:04:04'),
(290, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f110190>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:04'),
(291, 7, 0, 0.02869391441345215, '', NULL, '2025-07-07 16:04:04'),
(292, 1, 1, 0.044473, NULL, NULL, '2025-07-07 16:04:14'),
(293, 2, 1, 0.0011968612670898438, NULL, NULL, '2025-07-07 16:04:14'),
(294, 3, 1, 0.007420778274536133, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2896, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:14'),
(295, 4, 1, 0.02065896987915039, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5093, \"connections\": 2}', '2025-07-07 16:04:14'),
(296, 5, 0, 0.010621, NULL, NULL, '2025-07-07 16:04:14'),
(297, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f155610>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:14'),
(298, 7, 0, 0.0325167179107666, '', NULL, '2025-07-07 16:04:14'),
(299, 1, 1, 0.105939, NULL, NULL, '2025-07-07 16:04:24'),
(300, 2, 1, 0.0017333030700683594, NULL, NULL, '2025-07-07 16:04:24'),
(301, 3, 1, 0.008083105087280273, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2906, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:24'),
(302, 4, 1, 0.006987094879150391, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5103, \"connections\": 2}', '2025-07-07 16:04:24'),
(303, 5, 0, 0.006548, NULL, NULL, '2025-07-07 16:04:24'),
(304, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f15f890>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:24'),
(305, 7, 0, 0.0174558162689209, '', NULL, '2025-07-07 16:04:24'),
(306, 1, 1, 0.011656, NULL, NULL, '2025-07-07 16:04:34'),
(307, 2, 1, 0.001155853271484375, NULL, NULL, '2025-07-07 16:04:34'),
(308, 3, 1, 0.0096588134765625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2916, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:34'),
(309, 4, 1, 0.007837057113647461, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5113, \"connections\": 2}', '2025-07-07 16:04:34'),
(310, 5, 0, 0.014921, NULL, NULL, '2025-07-07 16:04:34'),
(311, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f15c110>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:34'),
(312, 7, 0, 0.019034147262573242, '', NULL, '2025-07-07 16:04:34'),
(313, 1, 1, 0.014585, NULL, NULL, '2025-07-07 16:04:44'),
(314, 2, 1, 0.0017910003662109375, NULL, NULL, '2025-07-07 16:04:44'),
(315, 3, 1, 0.013555288314819336, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2926, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:44'),
(316, 4, 1, 0.005789995193481445, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5123, \"connections\": 2}', '2025-07-07 16:04:44'),
(317, 5, 0, 0.007048, NULL, NULL, '2025-07-07 16:04:44'),
(318, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f238550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:44'),
(319, 7, 0, 0.020630836486816406, '', NULL, '2025-07-07 16:04:44'),
(320, 1, 1, 0.011148, NULL, NULL, '2025-07-07 16:04:54'),
(321, 2, 1, 0.0007181167602539062, NULL, NULL, '2025-07-07 16:04:54'),
(322, 3, 1, 0.00830698013305664, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2936, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:04:54'),
(323, 4, 1, 0.004878997802734375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5133, \"connections\": 2}', '2025-07-07 16:04:54'),
(324, 5, 0, 0.006178, NULL, NULL, '2025-07-07 16:04:54'),
(325, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f24a410>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:04:54'),
(326, 7, 0, 0.011727094650268555, '', NULL, '2025-07-07 16:04:54'),
(327, 1, 1, 0.021453, NULL, NULL, '2025-07-07 16:05:04'),
(328, 2, 1, 0.0010440349578857422, NULL, NULL, '2025-07-07 16:05:04'),
(329, 3, 1, 0.017179012298583984, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2946, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:04'),
(330, 4, 1, 0.013664960861206055, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5143, \"connections\": 2}', '2025-07-07 16:05:04'),
(331, 5, 0, 0.003871, NULL, NULL, '2025-07-07 16:05:04'),
(332, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f15da10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:04'),
(333, 7, 0, 0.07095909118652344, '', NULL, '2025-07-07 16:05:04'),
(334, 1, 1, 0.048553, NULL, NULL, '2025-07-07 16:05:14'),
(335, 2, 1, 0.0006349086761474609, NULL, NULL, '2025-07-07 16:05:14'),
(336, 3, 1, 0.012845993041992188, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2956, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:14'),
(337, 4, 1, 0.020940065383911133, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5153, \"connections\": 2}', '2025-07-07 16:05:14'),
(338, 5, 0, 0.030825, NULL, NULL, '2025-07-07 16:05:14'),
(339, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f15dd50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:14'),
(340, 7, 0, 0.032208919525146484, '', NULL, '2025-07-07 16:05:14'),
(341, 1, 1, 0.019226, NULL, NULL, '2025-07-07 16:05:24'),
(342, 2, 1, 0.0008757114410400391, NULL, NULL, '2025-07-07 16:05:24'),
(343, 3, 1, 0.01782512664794922, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2966, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:24'),
(344, 4, 1, 0.006949901580810547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5163, \"connections\": 2}', '2025-07-07 16:05:24'),
(345, 5, 0, 0.010404, NULL, NULL, '2025-07-07 16:05:24'),
(346, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f114dd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:24'),
(347, 7, 0, 0.06278014183044434, '', NULL, '2025-07-07 16:05:24'),
(348, 1, 1, 0.016295, NULL, NULL, '2025-07-07 16:05:34'),
(349, 2, 1, 0.0006909370422363281, NULL, NULL, '2025-07-07 16:05:34'),
(350, 3, 1, 0.02184295654296875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2976, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:34'),
(351, 4, 1, 0.007508039474487305, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5173, \"connections\": 2}', '2025-07-07 16:05:34'),
(352, 5, 0, 0.005089, NULL, NULL, '2025-07-07 16:05:34'),
(353, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f10ef50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:34'),
(354, 7, 0, 0.017136096954345703, '', NULL, '2025-07-07 16:05:34'),
(355, 1, 1, 0.024601, NULL, NULL, '2025-07-07 16:05:44'),
(356, 2, 1, 0.0005247592926025391, NULL, NULL, '2025-07-07 16:05:44'),
(357, 3, 1, 0.008378744125366211, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2986, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:44'),
(358, 4, 1, 0.002856016159057617, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5183, \"connections\": 2}', '2025-07-07 16:05:44'),
(359, 5, 0, 0.003993, NULL, NULL, '2025-07-07 16:05:44'),
(360, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1471d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:44'),
(361, 7, 0, 0.008726119995117188, '', NULL, '2025-07-07 16:05:44'),
(362, 1, 1, 0.016813, NULL, NULL, '2025-07-07 16:05:54'),
(363, 2, 1, 0.002232074737548828, NULL, NULL, '2025-07-07 16:05:54'),
(364, 3, 1, 0.007870912551879883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 2996, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:05:54'),
(365, 4, 1, 0.0030629634857177734, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5193, \"connections\": 2}', '2025-07-07 16:05:54'),
(366, 5, 0, 0.004847, NULL, NULL, '2025-07-07 16:05:54'),
(367, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f25a610>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:05:54'),
(368, 7, 0, 0.01694178581237793, '', NULL, '2025-07-07 16:05:54'),
(369, 1, 1, 0.045286, NULL, NULL, '2025-07-07 16:06:04'),
(370, 2, 1, 0.0021402835845947266, NULL, NULL, '2025-07-07 16:06:04'),
(371, 3, 1, 0.01680779457092285, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3006, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:06:04'),
(372, 4, 1, 0.004396200180053711, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5203, \"connections\": 2}', '2025-07-07 16:06:04'),
(373, 5, 0, 0.018001, NULL, NULL, '2025-07-07 16:06:04'),
(374, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f25ba90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:06:04'),
(375, 7, 0, 0.011779069900512695, '', NULL, '2025-07-07 16:06:04'),
(376, 1, 1, 0.066387, NULL, NULL, '2025-07-07 16:06:14'),
(377, 2, 1, 0.0017690658569335938, NULL, NULL, '2025-07-07 16:06:14'),
(378, 3, 1, 0.009794950485229492, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3016, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:06:14'),
(379, 4, 1, 0.015352010726928711, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5213, \"connections\": 2}', '2025-07-07 16:06:14'),
(380, 5, 0, 0.016573, NULL, NULL, '2025-07-07 16:06:14'),
(381, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f112350>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:06:14'),
(382, 7, 0, 0.026136159896850586, '', NULL, '2025-07-07 16:06:14'),
(383, 1, 1, 0.014076, NULL, NULL, '2025-07-07 16:06:43'),
(384, 2, 1, 0.0005822181701660156, NULL, NULL, '2025-07-07 16:06:43'),
(385, 3, 1, 0.008979082107543945, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3044, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:06:43'),
(386, 4, 1, 0.008330106735229492, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5242, \"connections\": 2}', '2025-07-07 16:06:43'),
(387, 5, 0, 0.004127, NULL, NULL, '2025-07-07 16:06:43'),
(388, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1fe110>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:06:43'),
(389, 7, 0, 0.01622605323791504, '', NULL, '2025-07-07 16:06:43');
INSERT INTO `service_logs` (`id`, `service_id`, `status`, `response_time`, `error_message`, `additional_data`, `checked_at`) VALUES
(390, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f23ab10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:06:52'),
(391, 1, 1, 0.020145, NULL, NULL, '2025-07-07 16:06:52'),
(392, 2, 1, 0.0009028911590576172, NULL, NULL, '2025-07-07 16:06:52'),
(393, 3, 1, 0.006997108459472656, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3054, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:06:52'),
(394, 4, 1, 0.00415802001953125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5251, \"connections\": 2}', '2025-07-07 16:06:52'),
(395, 5, 0, 0.004997, NULL, NULL, '2025-07-07 16:06:52'),
(396, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1bf8d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:06:52'),
(397, 7, 0, 0.009535074234008789, '', NULL, '2025-07-07 16:06:52'),
(398, 1, 1, 0.012075, NULL, NULL, '2025-07-07 16:06:56'),
(399, 2, 1, 0.0007359981536865234, NULL, NULL, '2025-07-07 16:07:00'),
(400, 1, 1, 0.020918, NULL, NULL, '2025-07-07 16:07:02'),
(401, 2, 1, 0.0006880760192871094, NULL, NULL, '2025-07-07 16:07:02'),
(402, 3, 1, 0.00844430923461914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3064, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:02'),
(403, 4, 1, 0.00470280647277832, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5261, \"connections\": 2}', '2025-07-07 16:07:02'),
(404, 5, 0, 0.013775, NULL, NULL, '2025-07-07 16:07:02'),
(405, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f238a50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:02'),
(406, 7, 0, 0.014447927474975586, '', NULL, '2025-07-07 16:07:02'),
(407, 4, 1, 0.00376129150390625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5262, \"connections\": 2}', '2025-07-07 16:07:03'),
(408, 3, 1, 0.008073806762695312, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3071, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:09'),
(409, 1, 1, 0.015613, NULL, NULL, '2025-07-07 16:07:12'),
(410, 2, 1, 0.01175379753112793, NULL, NULL, '2025-07-07 16:07:12'),
(411, 3, 1, 0.010642051696777344, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3074, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:12'),
(412, 4, 1, 0.005460023880004883, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5271, \"connections\": 2}', '2025-07-07 16:07:12'),
(413, 5, 0, 0.0047, NULL, NULL, '2025-07-07 16:07:12'),
(414, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f248e90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:12'),
(415, 7, 0, 0.007638692855834961, '', NULL, '2025-07-07 16:07:12'),
(416, 1, 1, 0.01703, NULL, NULL, '2025-07-07 16:07:22'),
(417, 2, 1, 0.0004711151123046875, NULL, NULL, '2025-07-07 16:07:22'),
(418, 3, 1, 0.0049741268157958984, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3084, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:22'),
(419, 4, 1, 0.006226301193237305, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5281, \"connections\": 2}', '2025-07-07 16:07:22'),
(420, 5, 0, 0.00461, NULL, NULL, '2025-07-07 16:07:22'),
(421, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f259350>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:22'),
(422, 7, 0, 0.008866071701049805, '', NULL, '2025-07-07 16:07:22'),
(423, 1, 1, 0.015673, NULL, NULL, '2025-07-07 16:07:32'),
(424, 2, 1, 0.0015993118286132812, NULL, NULL, '2025-07-07 16:07:32'),
(425, 3, 1, 0.007780790328979492, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3094, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:32'),
(426, 4, 1, 0.005482912063598633, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5291, \"connections\": 2}', '2025-07-07 16:07:32'),
(427, 5, 0, 0.00531, NULL, NULL, '2025-07-07 16:07:32'),
(428, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1fff10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:32'),
(429, 7, 0, 0.015504121780395508, '', NULL, '2025-07-07 16:07:32'),
(430, 1, 1, 0.01556, NULL, NULL, '2025-07-07 16:07:42'),
(431, 2, 1, 0.0013167858123779297, NULL, NULL, '2025-07-07 16:07:42'),
(432, 3, 1, 0.007503032684326172, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3104, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:42'),
(433, 4, 1, 0.005945920944213867, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5301, \"connections\": 2}', '2025-07-07 16:07:42'),
(434, 5, 0, 0.004825, NULL, NULL, '2025-07-07 16:07:42'),
(435, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f201090>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:42'),
(436, 7, 0, 0.008878946304321289, '', NULL, '2025-07-07 16:07:42'),
(437, 1, 1, 0.024252, NULL, NULL, '2025-07-07 16:07:52'),
(438, 2, 1, 0.002666950225830078, NULL, NULL, '2025-07-07 16:07:52'),
(439, 3, 1, 0.0071451663970947266, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3114, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:07:52'),
(440, 4, 1, 0.0031371116638183594, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5311, \"connections\": 2}', '2025-07-07 16:07:52'),
(441, 5, 0, 0.00376, NULL, NULL, '2025-07-07 16:07:52'),
(442, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f258990>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:07:52'),
(443, 7, 0, 0.009639263153076172, '', NULL, '2025-07-07 16:07:52'),
(444, 1, 1, 0.01023, NULL, NULL, '2025-07-07 16:08:04'),
(445, 2, 1, 0.0004901885986328125, NULL, NULL, '2025-07-07 16:08:04'),
(446, 3, 1, 0.00551915168762207, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3126, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:08:04'),
(447, 4, 1, 0.003464937210083008, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5323, \"connections\": 2}', '2025-07-07 16:08:04'),
(448, 5, 0, 0.003684, NULL, NULL, '2025-07-07 16:08:04'),
(449, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f1129d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:08:04'),
(450, 7, 0, 0.01071786880493164, '', NULL, '2025-07-07 16:08:04'),
(451, 1, 1, 0.013294, NULL, NULL, '2025-07-07 16:08:12'),
(452, 2, 1, 0.0008699893951416016, NULL, NULL, '2025-07-07 16:08:12'),
(453, 3, 1, 0.0052721500396728516, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3134, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:08:12'),
(454, 4, 1, 0.004043102264404297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5331, \"connections\": 2}', '2025-07-07 16:08:12'),
(455, 5, 0, 0.003486, NULL, NULL, '2025-07-07 16:08:12'),
(456, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f117c10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:08:12'),
(457, 7, 0, 0.016256093978881836, '', NULL, '2025-07-07 16:08:12'),
(458, 1, 1, 0.014097, NULL, NULL, '2025-07-07 16:08:22'),
(459, 2, 1, 0.0005388259887695312, NULL, NULL, '2025-07-07 16:08:22'),
(460, 3, 1, 0.006117105484008789, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3144, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:08:22'),
(461, 4, 1, 0.004055976867675781, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5341, \"connections\": 2}', '2025-07-07 16:08:22'),
(462, 5, 0, 0.003238, NULL, NULL, '2025-07-07 16:08:22'),
(463, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f23a310>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:08:22'),
(464, 7, 0, 0.0055201053619384766, '', NULL, '2025-07-07 16:08:22'),
(465, 1, 1, 0.015584, NULL, NULL, '2025-07-07 16:08:32'),
(466, 2, 1, 0.0010840892791748047, NULL, NULL, '2025-07-07 16:08:32'),
(467, 3, 1, 0.005643129348754883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3154, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:08:32'),
(468, 4, 1, 0.004967212677001953, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5351, \"connections\": 2}', '2025-07-07 16:08:32'),
(469, 5, 0, 0.003498, NULL, NULL, '2025-07-07 16:08:32'),
(470, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9000): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f184710>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:08:32'),
(471, 7, 0, 0.009476900100708008, '', NULL, '2025-07-07 16:08:32'),
(472, 1, 1, 0.013372, NULL, NULL, '2025-07-07 16:09:07'),
(473, 2, 1, 0.0005807876586914062, NULL, NULL, '2025-07-07 16:09:07'),
(474, 3, 1, 0.012114763259887695, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3189, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:07'),
(475, 4, 1, 0.009269952774047852, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5386, \"connections\": 2}', '2025-07-07 16:09:07'),
(476, 5, 0, 0.004557, NULL, NULL, '2025-07-07 16:09:07'),
(477, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9001): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f184710>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:09:07'),
(478, 7, 0, 0.01258993148803711, '', NULL, '2025-07-07 16:09:07'),
(479, 1, 1, 0.031623, NULL, NULL, '2025-07-07 16:09:09'),
(480, 2, 1, 0.000820159912109375, NULL, NULL, '2025-07-07 16:09:09'),
(481, 3, 1, 0.005797147750854492, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3191, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:09'),
(482, 4, 1, 0.0042798519134521484, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5388, \"connections\": 2}', '2025-07-07 16:09:09'),
(483, 5, 0, 0.004927, NULL, NULL, '2025-07-07 16:09:09'),
(484, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9001): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f184dd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:09:09'),
(485, 7, 0, 0.009912967681884766, '', NULL, '2025-07-07 16:09:09'),
(486, 1, 1, 0.026376, NULL, NULL, '2025-07-07 16:09:10'),
(487, 2, 1, 0.0005950927734375, NULL, NULL, '2025-07-07 16:09:10'),
(488, 3, 1, 0.009179830551147461, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3192, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:10'),
(489, 4, 1, 0.0036399364471435547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5389, \"connections\": 2}', '2025-07-07 16:09:10'),
(490, 5, 0, 0.005035, NULL, NULL, '2025-07-07 16:09:10'),
(491, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9001): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x10f185d10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-07 16:09:10'),
(492, 7, 0, 0.020299196243286133, '', NULL, '2025-07-07 16:09:11'),
(493, 1, 1, 0.014076, NULL, NULL, '2025-07-07 16:09:29'),
(494, 2, 1, 0.0007641315460205078, NULL, NULL, '2025-07-07 16:09:29'),
(495, 3, 1, 0.012716054916381836, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3211, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:29'),
(496, 4, 1, 0.007480144500732422, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5408, \"connections\": 2}', '2025-07-07 16:09:29'),
(497, 5, 0, 0.013917, NULL, NULL, '2025-07-07 16:09:29'),
(498, 6, 1, 0.023825, NULL, NULL, '2025-07-07 16:09:29'),
(499, 7, 0, 0.01520395278930664, '', NULL, '2025-07-07 16:09:29'),
(500, 1, 1, 0.0195, NULL, NULL, '2025-07-07 16:09:39'),
(501, 2, 1, 0.00084686279296875, NULL, NULL, '2025-07-07 16:09:39'),
(502, 3, 1, 0.0072901248931884766, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3221, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:39'),
(503, 4, 1, 0.004602909088134766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5418, \"connections\": 2}', '2025-07-07 16:09:39'),
(504, 5, 0, 0.009694, NULL, NULL, '2025-07-07 16:09:39'),
(505, 6, 1, 0.014032, NULL, NULL, '2025-07-07 16:09:39'),
(506, 7, 0, 0.016162872314453125, '', NULL, '2025-07-07 16:09:39'),
(507, 1, 1, 0.01538, NULL, NULL, '2025-07-07 16:09:55'),
(508, 2, 1, 0.0009551048278808594, NULL, NULL, '2025-07-07 16:09:55'),
(509, 3, 1, 0.007999181747436523, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3237, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:09:55'),
(510, 4, 1, 0.004099130630493164, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5434, \"connections\": 2}', '2025-07-07 16:09:55'),
(511, 5, 0, 0.004343, NULL, NULL, '2025-07-07 16:09:55'),
(512, 6, 1, 0.008184, NULL, NULL, '2025-07-07 16:09:55'),
(513, 7, 0, 0.017388105392456055, '', NULL, '2025-07-07 16:09:55'),
(514, 1, 1, 0.015247, NULL, NULL, '2025-07-07 16:10:00'),
(515, 2, 1, 0.002724885940551758, NULL, NULL, '2025-07-07 16:10:00'),
(516, 3, 1, 0.011217117309570312, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3242, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:00'),
(517, 4, 1, 0.004841804504394531, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5439, \"connections\": 2}', '2025-07-07 16:10:00'),
(518, 5, 0, 0.00615, NULL, NULL, '2025-07-07 16:10:00'),
(519, 6, 1, 0.008379, NULL, NULL, '2025-07-07 16:10:00'),
(520, 7, 0, 0.009525060653686523, '', NULL, '2025-07-07 16:10:00'),
(521, 1, 1, 0.013456, NULL, NULL, '2025-07-07 16:10:05'),
(522, 2, 1, 0.0004849433898925781, NULL, NULL, '2025-07-07 16:10:05'),
(523, 3, 1, 0.005282163619995117, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3247, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:05'),
(524, 4, 1, 0.0028617382049560547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5444, \"connections\": 2}', '2025-07-07 16:10:05'),
(525, 5, 0, 0.003425, NULL, NULL, '2025-07-07 16:10:05'),
(526, 6, 1, 0.004667, NULL, NULL, '2025-07-07 16:10:05'),
(527, 7, 0, 0.008829116821289062, '', NULL, '2025-07-07 16:10:05'),
(528, 1, 1, 0.011544, NULL, NULL, '2025-07-07 16:10:10'),
(529, 2, 1, 0.0007736682891845703, NULL, NULL, '2025-07-07 16:10:10'),
(530, 3, 1, 0.02143073081970215, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3252, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:10'),
(531, 4, 1, 0.017836809158325195, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5449, \"connections\": 2}', '2025-07-07 16:10:10'),
(532, 5, 0, 0.006462, NULL, NULL, '2025-07-07 16:10:10'),
(533, 6, 1, 0.009955, NULL, NULL, '2025-07-07 16:10:10'),
(534, 7, 0, 0.028989791870117188, '', NULL, '2025-07-07 16:10:10'),
(535, 1, 1, 0.015201, NULL, NULL, '2025-07-07 16:10:15'),
(536, 2, 1, 0.0013408660888671875, NULL, NULL, '2025-07-07 16:10:15'),
(537, 3, 1, 0.006289958953857422, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3257, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:15'),
(538, 4, 1, 0.0037589073181152344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5454, \"connections\": 2}', '2025-07-07 16:10:15'),
(539, 5, 0, 0.00385, NULL, NULL, '2025-07-07 16:10:15'),
(540, 6, 1, 0.00452, NULL, NULL, '2025-07-07 16:10:15'),
(541, 7, 0, 0.007814884185791016, '', NULL, '2025-07-07 16:10:15'),
(542, 1, 1, 0.016082, NULL, NULL, '2025-07-07 16:10:20'),
(543, 2, 1, 0.0008351802825927734, NULL, NULL, '2025-07-07 16:10:20'),
(544, 3, 1, 0.0073549747467041016, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3262, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:20'),
(545, 4, 1, 0.0035161972045898438, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5459, \"connections\": 2}', '2025-07-07 16:10:20'),
(546, 5, 0, 0.003763, NULL, NULL, '2025-07-07 16:10:20'),
(547, 6, 1, 0.004591, NULL, NULL, '2025-07-07 16:10:20'),
(548, 7, 0, 0.01666402816772461, '', NULL, '2025-07-07 16:10:20'),
(549, 1, 1, 0.013014, NULL, NULL, '2025-07-07 16:10:25'),
(550, 2, 1, 0.0005030632019042969, NULL, NULL, '2025-07-07 16:10:25'),
(551, 3, 1, 0.004861116409301758, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3267, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:25'),
(552, 4, 1, 0.002833843231201172, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5464, \"connections\": 2}', '2025-07-07 16:10:25'),
(553, 5, 0, 0.003097, NULL, NULL, '2025-07-07 16:10:25'),
(554, 6, 1, 0.003315, NULL, NULL, '2025-07-07 16:10:25'),
(555, 7, 0, 0.008640766143798828, '', NULL, '2025-07-07 16:10:25'),
(556, 1, 1, 0.016538, NULL, NULL, '2025-07-07 16:10:30'),
(557, 2, 1, 0.0008361339569091797, NULL, NULL, '2025-07-07 16:10:30'),
(558, 3, 1, 0.006360054016113281, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3272, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:30'),
(559, 4, 1, 0.0032532215118408203, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5469, \"connections\": 2}', '2025-07-07 16:10:30'),
(560, 5, 0, 0.003717, NULL, NULL, '2025-07-07 16:10:30'),
(561, 6, 1, 0.005802, NULL, NULL, '2025-07-07 16:10:30'),
(562, 7, 0, 0.01101994514465332, '', NULL, '2025-07-07 16:10:30'),
(563, 1, 1, 0.007951, NULL, NULL, '2025-07-07 16:10:35'),
(564, 2, 1, 0.0004868507385253906, NULL, NULL, '2025-07-07 16:10:35'),
(565, 3, 1, 0.010083198547363281, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3277, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:35'),
(566, 4, 1, 0.004564046859741211, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5474, \"connections\": 2}', '2025-07-07 16:10:35'),
(567, 5, 0, 0.004085, NULL, NULL, '2025-07-07 16:10:35'),
(568, 6, 1, 0.00348, NULL, NULL, '2025-07-07 16:10:35'),
(569, 7, 0, 0.008282899856567383, '', NULL, '2025-07-07 16:10:35'),
(570, 1, 1, 0.012425, NULL, NULL, '2025-07-07 16:10:40'),
(571, 2, 1, 0.0004699230194091797, NULL, NULL, '2025-07-07 16:10:40'),
(572, 3, 1, 0.006698131561279297, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3282, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:40'),
(573, 4, 1, 0.003835916519165039, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5479, \"connections\": 2}', '2025-07-07 16:10:40'),
(574, 5, 0, 0.005307, NULL, NULL, '2025-07-07 16:10:40'),
(575, 6, 1, 0.004536, NULL, NULL, '2025-07-07 16:10:40'),
(576, 7, 0, 0.009467124938964844, '', NULL, '2025-07-07 16:10:40'),
(577, 1, 1, 0.015558, NULL, NULL, '2025-07-07 16:10:45'),
(578, 2, 1, 0.004077911376953125, NULL, NULL, '2025-07-07 16:10:45'),
(579, 3, 1, 0.0065898895263671875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3287, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:45'),
(580, 4, 1, 0.003206968307495117, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5484, \"connections\": 2}', '2025-07-07 16:10:45'),
(581, 5, 0, 0.003961, NULL, NULL, '2025-07-07 16:10:45'),
(582, 6, 1, 0.004316, NULL, NULL, '2025-07-07 16:10:45'),
(583, 7, 0, 0.012327909469604492, '', NULL, '2025-07-07 16:10:45'),
(584, 1, 1, 0.014783, NULL, NULL, '2025-07-07 16:10:50'),
(585, 2, 1, 0.004928112030029297, NULL, NULL, '2025-07-07 16:10:50'),
(586, 3, 1, 0.006989717483520508, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3292, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:50'),
(587, 4, 1, 0.003256082534790039, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5489, \"connections\": 2}', '2025-07-07 16:10:50'),
(588, 5, 0, 0.005938, NULL, NULL, '2025-07-07 16:10:50'),
(589, 6, 1, 0.004566, NULL, NULL, '2025-07-07 16:10:50'),
(590, 7, 0, 0.011348962783813477, '', NULL, '2025-07-07 16:10:50'),
(591, 1, 1, 0.015117, NULL, NULL, '2025-07-07 16:10:55'),
(592, 2, 1, 0.0007388591766357422, NULL, NULL, '2025-07-07 16:10:55'),
(593, 3, 1, 0.0063343048095703125, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3297, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:10:55'),
(594, 4, 1, 0.003381013870239258, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5494, \"connections\": 2}', '2025-07-07 16:10:55'),
(595, 5, 0, 0.004364, NULL, NULL, '2025-07-07 16:10:55'),
(596, 6, 1, 0.004739, NULL, NULL, '2025-07-07 16:10:55'),
(597, 7, 0, 0.009682893753051758, '', NULL, '2025-07-07 16:10:55'),
(598, 1, 1, 0.012316, NULL, NULL, '2025-07-07 16:11:00'),
(599, 2, 1, 0.00047516822814941406, NULL, NULL, '2025-07-07 16:11:00'),
(600, 3, 1, 0.0067560672760009766, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3302, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:00'),
(601, 4, 1, 0.0034942626953125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5499, \"connections\": 2}', '2025-07-07 16:11:00'),
(602, 5, 0, 0.00433, NULL, NULL, '2025-07-07 16:11:00'),
(603, 6, 1, 0.005215, NULL, NULL, '2025-07-07 16:11:00'),
(604, 7, 0, 0.011867761611938477, '', NULL, '2025-07-07 16:11:00'),
(605, 1, 1, 0.021175, NULL, NULL, '2025-07-07 16:11:05'),
(606, 2, 1, 0.0009629726409912109, NULL, NULL, '2025-07-07 16:11:05'),
(607, 3, 1, 0.00841665267944336, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3307, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:05'),
(608, 4, 1, 0.0037529468536376953, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5504, \"connections\": 2}', '2025-07-07 16:11:05'),
(609, 5, 0, 0.004471, NULL, NULL, '2025-07-07 16:11:05'),
(610, 6, 1, 0.005022, NULL, NULL, '2025-07-07 16:11:05'),
(611, 7, 0, 0.016637086868286133, '', NULL, '2025-07-07 16:11:05'),
(612, 1, 1, 0.010845, NULL, NULL, '2025-07-07 16:11:10'),
(613, 2, 1, 0.00061798095703125, NULL, NULL, '2025-07-07 16:11:10'),
(614, 3, 1, 0.006316184997558594, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3312, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:10'),
(615, 4, 1, 0.004070758819580078, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5509, \"connections\": 2}', '2025-07-07 16:11:10'),
(616, 5, 0, 0.004744, NULL, NULL, '2025-07-07 16:11:10'),
(617, 6, 1, 0.004475, NULL, NULL, '2025-07-07 16:11:10'),
(618, 7, 0, 0.009525775909423828, '', NULL, '2025-07-07 16:11:10'),
(619, 1, 1, 0.01271, NULL, NULL, '2025-07-07 16:11:15'),
(620, 2, 1, 0.0007011890411376953, NULL, NULL, '2025-07-07 16:11:15'),
(621, 3, 1, 0.005109071731567383, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3317, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:15'),
(622, 4, 1, 0.0029990673065185547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5514, \"connections\": 2}', '2025-07-07 16:11:15'),
(623, 5, 0, 0.00357, NULL, NULL, '2025-07-07 16:11:15'),
(624, 6, 1, 0.004532, NULL, NULL, '2025-07-07 16:11:15'),
(625, 7, 0, 0.007967948913574219, '', NULL, '2025-07-07 16:11:15'),
(626, 1, 1, 0.012401, NULL, NULL, '2025-07-07 16:11:20'),
(627, 2, 1, 0.0013842582702636719, NULL, NULL, '2025-07-07 16:11:20'),
(628, 3, 1, 0.006727933883666992, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3322, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:20'),
(629, 4, 1, 0.0039098262786865234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5519, \"connections\": 2}', '2025-07-07 16:11:20'),
(630, 5, 0, 0.00394, NULL, NULL, '2025-07-07 16:11:20'),
(631, 6, 1, 0.004748, NULL, NULL, '2025-07-07 16:11:20'),
(632, 7, 0, 0.008194923400878906, '', NULL, '2025-07-07 16:11:20'),
(633, 1, 1, 0.012812, NULL, NULL, '2025-07-07 16:11:25'),
(634, 2, 1, 0.0004918575286865234, NULL, NULL, '2025-07-07 16:11:25'),
(635, 3, 1, 0.006761074066162109, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3327, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:25'),
(636, 4, 1, 0.003283977508544922, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5524, \"connections\": 2}', '2025-07-07 16:11:25'),
(637, 5, 0, 0.003831, NULL, NULL, '2025-07-07 16:11:25'),
(638, 6, 1, 0.004169, NULL, NULL, '2025-07-07 16:11:25'),
(639, 7, 0, 0.005636930465698242, '', NULL, '2025-07-07 16:11:25'),
(640, 1, 1, 0.010871, NULL, NULL, '2025-07-07 16:11:30'),
(641, 2, 1, 0.002788066864013672, NULL, NULL, '2025-07-07 16:11:30'),
(642, 3, 1, 0.007459878921508789, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3332, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:30'),
(643, 4, 1, 0.004535198211669922, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5529, \"connections\": 2}', '2025-07-07 16:11:30'),
(644, 5, 0, 0.003511, NULL, NULL, '2025-07-07 16:11:30'),
(645, 6, 1, 0.004016, NULL, NULL, '2025-07-07 16:11:30'),
(646, 7, 0, 0.010187864303588867, '', NULL, '2025-07-07 16:11:30'),
(647, 1, 1, 0.011742, NULL, NULL, '2025-07-07 16:11:35'),
(648, 2, 1, 0.001348257064819336, NULL, NULL, '2025-07-07 16:11:35'),
(649, 3, 1, 0.0067310333251953125, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3337, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:35'),
(650, 4, 1, 0.0035719871520996094, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5534, \"connections\": 2}', '2025-07-07 16:11:35'),
(651, 5, 0, 0.003767, NULL, NULL, '2025-07-07 16:11:35'),
(652, 6, 1, 0.003554, NULL, NULL, '2025-07-07 16:11:35'),
(653, 7, 0, 0.00887608528137207, '', NULL, '2025-07-07 16:11:35'),
(654, 1, 1, 0.010863, NULL, NULL, '2025-07-07 16:11:40'),
(655, 2, 1, 0.0006470680236816406, NULL, NULL, '2025-07-07 16:11:40'),
(656, 3, 1, 0.006001949310302734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3342, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:40'),
(657, 4, 1, 0.0029959678649902344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5539, \"connections\": 2}', '2025-07-07 16:11:40'),
(658, 5, 0, 0.003589, NULL, NULL, '2025-07-07 16:11:40'),
(659, 6, 1, 0.004868, NULL, NULL, '2025-07-07 16:11:40'),
(660, 7, 0, 0.00865626335144043, '', NULL, '2025-07-07 16:11:40'),
(661, 1, 1, 0.013031, NULL, NULL, '2025-07-07 16:11:45'),
(662, 2, 1, 0.0011839866638183594, NULL, NULL, '2025-07-07 16:11:45'),
(663, 3, 1, 0.005074024200439453, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3347, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:45'),
(664, 4, 1, 0.002752065658569336, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5544, \"connections\": 2}', '2025-07-07 16:11:45'),
(665, 5, 0, 0.003598, NULL, NULL, '2025-07-07 16:11:45'),
(666, 6, 1, 0.003558, NULL, NULL, '2025-07-07 16:11:45'),
(667, 7, 0, 0.008904218673706055, '', NULL, '2025-07-07 16:11:45'),
(668, 1, 1, 0.008904, NULL, NULL, '2025-07-07 16:11:50'),
(669, 2, 1, 0.0004820823669433594, NULL, NULL, '2025-07-07 16:11:50'),
(670, 3, 1, 0.006053924560546875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3352, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:50'),
(671, 4, 1, 0.0035238265991210938, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5549, \"connections\": 2}', '2025-07-07 16:11:50'),
(672, 5, 0, 0.00433, NULL, NULL, '2025-07-07 16:11:50'),
(673, 6, 1, 0.004418, NULL, NULL, '2025-07-07 16:11:50'),
(674, 7, 0, 0.007966995239257812, '', NULL, '2025-07-07 16:11:50'),
(675, 1, 1, 0.010248, NULL, NULL, '2025-07-07 16:11:55'),
(676, 2, 1, 0.0005428791046142578, NULL, NULL, '2025-07-07 16:11:55'),
(677, 3, 1, 0.0054018497467041016, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3357, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:11:55'),
(678, 4, 1, 0.0032949447631835938, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5554, \"connections\": 2}', '2025-07-07 16:11:55'),
(679, 5, 0, 0.003502, NULL, NULL, '2025-07-07 16:11:55'),
(680, 6, 1, 0.007286, NULL, NULL, '2025-07-07 16:11:55'),
(681, 7, 0, 0.007308006286621094, '', NULL, '2025-07-07 16:11:55'),
(682, 1, 1, 0.01083, NULL, NULL, '2025-07-07 16:12:00'),
(683, 2, 1, 0.0005130767822265625, NULL, NULL, '2025-07-07 16:12:00'),
(684, 3, 1, 0.0053861141204833984, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3362, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:00'),
(685, 4, 1, 0.0027740001678466797, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5559, \"connections\": 2}', '2025-07-07 16:12:00'),
(686, 5, 0, 0.003635, NULL, NULL, '2025-07-07 16:12:00'),
(687, 6, 1, 0.004072, NULL, NULL, '2025-07-07 16:12:00'),
(688, 7, 0, 0.008151769638061523, '', NULL, '2025-07-07 16:12:00'),
(689, 1, 1, 0.011534, NULL, NULL, '2025-07-07 16:12:05'),
(690, 2, 1, 0.0005469322204589844, NULL, NULL, '2025-07-07 16:12:05'),
(691, 3, 1, 0.005122184753417969, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3367, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:05'),
(692, 4, 1, 0.0028128623962402344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5564, \"connections\": 2}', '2025-07-07 16:12:05'),
(693, 5, 0, 0.003282, NULL, NULL, '2025-07-07 16:12:05'),
(694, 6, 1, 0.003415, NULL, NULL, '2025-07-07 16:12:05'),
(695, 7, 0, 0.008139848709106445, '', NULL, '2025-07-07 16:12:05'),
(696, 1, 1, 0.009308, NULL, NULL, '2025-07-07 16:12:10'),
(697, 2, 1, 0.00045299530029296875, NULL, NULL, '2025-07-07 16:12:10'),
(698, 3, 1, 0.005262851715087891, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3372, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:10'),
(699, 4, 1, 0.0027582645416259766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5569, \"connections\": 2}', '2025-07-07 16:12:10'),
(700, 5, 0, 0.003511, NULL, NULL, '2025-07-07 16:12:10'),
(701, 6, 1, 0.004622, NULL, NULL, '2025-07-07 16:12:10'),
(702, 7, 0, 0.007550954818725586, '', NULL, '2025-07-07 16:12:10'),
(703, 1, 1, 0.013484, NULL, NULL, '2025-07-07 16:12:15'),
(704, 2, 1, 0.0037560462951660156, NULL, NULL, '2025-07-07 16:12:15'),
(705, 3, 1, 0.007596254348754883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3377, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:15'),
(706, 4, 1, 0.003875732421875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5574, \"connections\": 2}', '2025-07-07 16:12:15'),
(707, 5, 0, 0.006233, NULL, NULL, '2025-07-07 16:12:15'),
(708, 6, 1, 0.004691, NULL, NULL, '2025-07-07 16:12:15'),
(709, 7, 0, 0.013534784317016602, '', NULL, '2025-07-07 16:12:15'),
(710, 1, 1, 0.013146, NULL, NULL, '2025-07-07 16:12:20'),
(711, 2, 1, 0.0004899501800537109, NULL, NULL, '2025-07-07 16:12:20'),
(712, 3, 1, 0.005606889724731445, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3382, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:20'),
(713, 4, 1, 0.0029230117797851562, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5579, \"connections\": 2}', '2025-07-07 16:12:20'),
(714, 5, 0, 0.003584, NULL, NULL, '2025-07-07 16:12:20'),
(715, 6, 1, 0.003918, NULL, NULL, '2025-07-07 16:12:20'),
(716, 7, 0, 0.0077817440032958984, '', NULL, '2025-07-07 16:12:20'),
(717, 1, 1, 0.014239, NULL, NULL, '2025-07-07 16:12:25'),
(718, 2, 1, 0.0029108524322509766, NULL, NULL, '2025-07-07 16:12:25'),
(719, 3, 1, 0.0063838958740234375, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3387, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:25'),
(720, 4, 1, 0.003859996795654297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5584, \"connections\": 2}', '2025-07-07 16:12:25'),
(721, 5, 0, 0.004176, NULL, NULL, '2025-07-07 16:12:25'),
(722, 6, 1, 0.003679, NULL, NULL, '2025-07-07 16:12:25'),
(723, 7, 0, 0.0071277618408203125, '', NULL, '2025-07-07 16:12:25'),
(724, 1, 1, 0.012776, NULL, NULL, '2025-07-07 16:12:30'),
(725, 2, 1, 0.0011410713195800781, NULL, NULL, '2025-07-07 16:12:30'),
(726, 3, 1, 0.00584721565246582, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3392, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:30'),
(727, 4, 1, 0.003524303436279297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5589, \"connections\": 2}', '2025-07-07 16:12:30'),
(728, 5, 0, 0.005994, NULL, NULL, '2025-07-07 16:12:30'),
(729, 6, 1, 0.004104, NULL, NULL, '2025-07-07 16:12:30'),
(730, 7, 0, 0.005127906799316406, '', NULL, '2025-07-07 16:12:30'),
(731, 1, 1, 0.008383, NULL, NULL, '2025-07-07 16:12:35'),
(732, 2, 1, 0.004262208938598633, NULL, NULL, '2025-07-07 16:12:35'),
(733, 3, 1, 0.007526874542236328, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3397, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:35'),
(734, 4, 1, 0.0034182071685791016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5594, \"connections\": 2}', '2025-07-07 16:12:35'),
(735, 5, 0, 0.003727, NULL, NULL, '2025-07-07 16:12:35'),
(736, 6, 1, 0.00443, NULL, NULL, '2025-07-07 16:12:35'),
(737, 7, 0, 0.014904022216796875, '', NULL, '2025-07-07 16:12:35'),
(738, 1, 1, 0.012625, NULL, NULL, '2025-07-07 16:12:40'),
(739, 2, 1, 0.0006961822509765625, NULL, NULL, '2025-07-07 16:12:40'),
(740, 3, 1, 0.0057408809661865234, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3402, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:40'),
(741, 4, 1, 0.002847909927368164, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5599, \"connections\": 2}', '2025-07-07 16:12:40'),
(742, 5, 0, 0.004574, NULL, NULL, '2025-07-07 16:12:40'),
(743, 6, 1, 0.00371, NULL, NULL, '2025-07-07 16:12:40'),
(744, 7, 0, 0.00809621810913086, '', NULL, '2025-07-07 16:12:40'),
(745, 1, 1, 0.009045, NULL, NULL, '2025-07-07 16:12:45'),
(746, 2, 1, 0.0010280609130859375, NULL, NULL, '2025-07-07 16:12:45'),
(747, 3, 1, 0.007114887237548828, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3407, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:45'),
(748, 4, 1, 0.0033180713653564453, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5604, \"connections\": 2}', '2025-07-07 16:12:45'),
(749, 5, 0, 0.003757, NULL, NULL, '2025-07-07 16:12:45'),
(750, 6, 1, 0.004601, NULL, NULL, '2025-07-07 16:12:45'),
(751, 7, 0, 0.007848262786865234, '', NULL, '2025-07-07 16:12:45'),
(752, 1, 1, 0.007313, NULL, NULL, '2025-07-07 16:12:50'),
(753, 2, 1, 0.0008862018585205078, NULL, NULL, '2025-07-07 16:12:50'),
(754, 3, 1, 0.0067288875579833984, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3412, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:50'),
(755, 4, 1, 0.00404667854309082, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5609, \"connections\": 2}', '2025-07-07 16:12:50'),
(756, 5, 0, 0.004017, NULL, NULL, '2025-07-07 16:12:50'),
(757, 6, 1, 0.004076, NULL, NULL, '2025-07-07 16:12:50'),
(758, 7, 0, 0.0075380802154541016, '', NULL, '2025-07-07 16:12:50'),
(759, 1, 1, 0.009198, NULL, NULL, '2025-07-07 16:12:55'),
(760, 2, 1, 0.0004878044128417969, NULL, NULL, '2025-07-07 16:12:55'),
(761, 3, 1, 0.005020856857299805, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3417, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:12:55'),
(762, 4, 1, 0.0030059814453125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5614, \"connections\": 2}', '2025-07-07 16:12:55'),
(763, 5, 0, 0.003748, NULL, NULL, '2025-07-07 16:12:55'),
(764, 6, 1, 0.004144, NULL, NULL, '2025-07-07 16:12:55'),
(765, 7, 0, 0.008125782012939453, '', NULL, '2025-07-07 16:12:55'),
(766, 1, 1, 0.009829, NULL, NULL, '2025-07-07 16:13:00'),
(767, 2, 1, 0.0011119842529296875, NULL, NULL, '2025-07-07 16:13:00'),
(768, 3, 1, 0.005059719085693359, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3422, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:00'),
(769, 4, 1, 0.002755880355834961, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5619, \"connections\": 2}', '2025-07-07 16:13:00'),
(770, 5, 0, 0.004266, NULL, NULL, '2025-07-07 16:13:00'),
(771, 6, 1, 0.004118, NULL, NULL, '2025-07-07 16:13:00'),
(772, 7, 0, 0.005400180816650391, '', NULL, '2025-07-07 16:13:00'),
(773, 1, 1, 0.014487, NULL, NULL, '2025-07-07 16:13:05'),
(774, 2, 1, 0.0005180835723876953, NULL, NULL, '2025-07-07 16:13:05'),
(775, 3, 1, 0.007776021957397461, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3427, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:05'),
(776, 4, 1, 0.006341218948364258, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5624, \"connections\": 2}', '2025-07-07 16:13:05'),
(777, 5, 0, 0.00919, NULL, NULL, '2025-07-07 16:13:05'),
(778, 6, 1, 0.006168, NULL, NULL, '2025-07-07 16:13:05'),
(779, 7, 0, 0.02399420738220215, '', NULL, '2025-07-07 16:13:05'),
(780, 1, 1, 0.01376, NULL, NULL, '2025-07-07 16:13:10'),
(781, 2, 1, 0.0005407333374023438, NULL, NULL, '2025-07-07 16:13:10'),
(782, 3, 1, 0.012117147445678711, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3432, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:10'),
(783, 4, 1, 0.0075550079345703125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5629, \"connections\": 2}', '2025-07-07 16:13:10'),
(784, 5, 0, 0.014421, NULL, NULL, '2025-07-07 16:13:10'),
(785, 6, 1, 0.013968, NULL, NULL, '2025-07-07 16:13:10'),
(786, 7, 0, 0.03954911231994629, '', NULL, '2025-07-07 16:13:10'),
(787, 1, 1, 0.012371, NULL, NULL, '2025-07-07 16:13:15'),
(788, 2, 1, 0.005269050598144531, NULL, NULL, '2025-07-07 16:13:15'),
(789, 3, 1, 0.0069010257720947266, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3437, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:15'),
(790, 4, 1, 0.003987789154052734, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5634, \"connections\": 2}', '2025-07-07 16:13:15'),
(791, 5, 0, 0.005761, NULL, NULL, '2025-07-07 16:13:15'),
(792, 6, 1, 0.00398, NULL, NULL, '2025-07-07 16:13:15'),
(793, 7, 0, 0.012618064880371094, '', NULL, '2025-07-07 16:13:15'),
(794, 1, 1, 0.015531, NULL, NULL, '2025-07-07 16:13:20'),
(795, 2, 1, 0.0005309581756591797, NULL, NULL, '2025-07-07 16:13:20'),
(796, 3, 1, 0.01102590560913086, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3442, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:20'),
(797, 4, 1, 0.0029392242431640625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5639, \"connections\": 2}', '2025-07-07 16:13:20'),
(798, 5, 0, 0.003456, NULL, NULL, '2025-07-07 16:13:20'),
(799, 6, 1, 0.005325, NULL, NULL, '2025-07-07 16:13:20'),
(800, 7, 0, 0.009685039520263672, '', NULL, '2025-07-07 16:13:20'),
(801, 1, 1, 0.020703, NULL, NULL, '2025-07-07 16:13:25'),
(802, 2, 1, 0.0008351802825927734, NULL, NULL, '2025-07-07 16:13:25'),
(803, 3, 1, 0.010368108749389648, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3447, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:25'),
(804, 4, 1, 0.00492095947265625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5644, \"connections\": 2}', '2025-07-07 16:13:25'),
(805, 5, 0, 0.005947, NULL, NULL, '2025-07-07 16:13:25'),
(806, 6, 1, 0.004048, NULL, NULL, '2025-07-07 16:13:25'),
(807, 7, 0, 0.009295225143432617, '', NULL, '2025-07-07 16:13:25'),
(808, 1, 1, 0.008341, NULL, NULL, '2025-07-07 16:13:30'),
(809, 2, 1, 0.0004649162292480469, NULL, NULL, '2025-07-07 16:13:30'),
(810, 3, 1, 0.006259918212890625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3452, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:30'),
(811, 4, 1, 0.0030498504638671875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5649, \"connections\": 2}', '2025-07-07 16:13:30'),
(812, 5, 0, 0.003524, NULL, NULL, '2025-07-07 16:13:30'),
(813, 6, 1, 0.005429, NULL, NULL, '2025-07-07 16:13:30'),
(814, 7, 0, 0.012868165969848633, '', NULL, '2025-07-07 16:13:30'),
(815, 1, 1, 0.022556, NULL, NULL, '2025-07-07 16:13:32'),
(816, 2, 1, 0.0005657672882080078, NULL, NULL, '2025-07-07 16:13:32'),
(817, 3, 1, 0.006768226623535156, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3454, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:32'),
(818, 4, 1, 0.003921031951904297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5651, \"connections\": 2}', '2025-07-07 16:13:32'),
(819, 5, 0, 0.004886, NULL, NULL, '2025-07-07 16:13:32'),
(820, 6, 1, 0.004717, NULL, NULL, '2025-07-07 16:13:32'),
(821, 7, 0, 0.012972116470336914, '', NULL, '2025-07-07 16:13:32'),
(822, 1, 1, 0.011507, NULL, NULL, '2025-07-07 16:13:33'),
(823, 2, 1, 0.001689910888671875, NULL, NULL, '2025-07-07 16:13:33'),
(824, 3, 1, 0.007275104522705078, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3455, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:33'),
(825, 4, 1, 0.005599021911621094, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5652, \"connections\": 2}', '2025-07-07 16:13:33'),
(826, 5, 0, 0.008129, NULL, NULL, '2025-07-07 16:13:33'),
(827, 6, 1, 0.006349, NULL, NULL, '2025-07-07 16:13:33'),
(828, 7, 0, 0.019140958786010742, '', NULL, '2025-07-07 16:13:33'),
(829, 1, 1, 0.027984, NULL, NULL, '2025-07-07 16:13:34'),
(830, 2, 1, 0.0015511512756347656, NULL, NULL, '2025-07-07 16:13:34'),
(831, 3, 1, 0.008615970611572266, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3456, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:34'),
(832, 4, 1, 0.0042057037353515625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5653, \"connections\": 2}', '2025-07-07 16:13:34'),
(833, 5, 0, 0.007253, NULL, NULL, '2025-07-07 16:13:34'),
(834, 6, 1, 0.030296, NULL, NULL, '2025-07-07 16:13:34'),
(835, 7, 0, 0.016997098922729492, '', NULL, '2025-07-07 16:13:34'),
(836, 1, 1, 0.015899, NULL, NULL, '2025-07-07 16:13:35'),
(837, 2, 1, 0.0007841587066650391, NULL, NULL, '2025-07-07 16:13:35'),
(838, 3, 1, 0.007447004318237305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3457, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:35'),
(839, 4, 1, 0.0059261322021484375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5654, \"connections\": 2}', '2025-07-07 16:13:35'),
(840, 5, 0, 0.005439, NULL, NULL, '2025-07-07 16:13:35'),
(841, 6, 1, 0.005763, NULL, NULL, '2025-07-07 16:13:35'),
(842, 7, 0, 0.011804342269897461, '', NULL, '2025-07-07 16:13:35'),
(843, 1, 1, 0.021629, NULL, NULL, '2025-07-07 16:13:52'),
(844, 2, 1, 0.0008480548858642578, NULL, NULL, '2025-07-07 16:13:52'),
(845, 3, 1, 0.011777162551879883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3474, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:13:52'),
(846, 4, 1, 0.00652313232421875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5671, \"connections\": 2}', '2025-07-07 16:13:52'),
(847, 5, 0, 0.006705, NULL, NULL, '2025-07-07 16:13:52'),
(848, 6, 1, 0.004467, NULL, NULL, '2025-07-07 16:13:52'),
(849, 7, 0, 0.018246889114379883, '', NULL, '2025-07-07 16:13:52'),
(850, 1, 1, 0.010729, NULL, NULL, '2025-07-07 16:14:18'),
(851, 2, 1, 0.0007488727569580078, NULL, NULL, '2025-07-07 16:14:18'),
(852, 3, 1, 0.007403135299682617, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3500, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:14:18'),
(853, 4, 1, 0.005308866500854492, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5697, \"connections\": 2}', '2025-07-07 16:14:18'),
(854, 5, 0, 0.004419, NULL, NULL, '2025-07-07 16:14:18'),
(855, 6, 1, 0.008413, NULL, NULL, '2025-07-07 16:14:18'),
(856, 7, 0, 0.061286211013793945, '', NULL, '2025-07-07 16:14:18'),
(857, 5, 0, 0.020494, NULL, NULL, '2025-07-07 16:14:27'),
(858, 1, 1, 0.018025, NULL, NULL, '2025-07-07 16:14:28'),
(859, 2, 1, 0.0005838871002197266, NULL, NULL, '2025-07-07 16:14:28'),
(860, 3, 1, 0.012553215026855469, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3510, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:14:28'),
(861, 4, 1, 0.004644870758056641, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5707, \"connections\": 2}', '2025-07-07 16:14:28'),
(862, 5, 0, 0.00469, NULL, NULL, '2025-07-07 16:14:28'),
(863, 6, 1, 0.004174, NULL, NULL, '2025-07-07 16:14:28'),
(864, 7, 0, 0.02364206314086914, '', NULL, '2025-07-07 16:14:28'),
(865, 1, 1, 0.025841, NULL, NULL, '2025-07-07 16:14:38'),
(866, 2, 1, 0.003276824951171875, NULL, NULL, '2025-07-07 16:14:38'),
(867, 3, 1, 0.012780904769897461, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3520, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:14:38'),
(868, 4, 1, 0.005851030349731445, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5717, \"connections\": 2}', '2025-07-07 16:14:38'),
(869, 5, 0, 0.004868, NULL, NULL, '2025-07-07 16:14:38'),
(870, 6, 1, 0.008863, NULL, NULL, '2025-07-07 16:14:38'),
(871, 7, 0, 0.017049074172973633, '', NULL, '2025-07-07 16:14:38'),
(872, 1, 1, 0.023442, NULL, NULL, '2025-07-07 16:14:48'),
(873, 2, 1, 0.0014967918395996094, NULL, NULL, '2025-07-07 16:14:48'),
(874, 3, 1, 0.011120796203613281, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3530, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:14:48'),
(875, 4, 1, 0.017495155334472656, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 5727, \"connections\": 2}', '2025-07-07 16:14:48'),
(876, 5, 0, 0.008857, NULL, NULL, '2025-07-07 16:14:48'),
(877, 6, 1, 0.004529, NULL, NULL, '2025-07-07 16:14:48'),
(878, 7, 0, 0.016054868698120117, '', NULL, '2025-07-07 16:14:48'),
(879, 1, 1, 0.017429, NULL, NULL, '2025-07-07 16:27:32'),
(880, 2, 1, 0.00055694580078125, NULL, NULL, '2025-07-07 16:27:32'),
(881, 3, 1, 0.010391950607299805, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4294, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:27:32'),
(882, 4, 1, 0.003604888916015625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6491, \"connections\": 2}', '2025-07-07 16:27:32'),
(883, 5, 0, 0.005065, NULL, NULL, '2025-07-07 16:27:32'),
(884, 6, 1, 0.01012, NULL, NULL, '2025-07-07 16:27:32'),
(885, 7, 0, 0.07314920425415039, '', NULL, '2025-07-07 16:27:32'),
(886, 1, 1, 0.035084, NULL, NULL, '2025-07-07 16:34:17'),
(887, 2, 1, 0.001664876937866211, NULL, NULL, '2025-07-07 16:34:17'),
(888, 3, 1, 0.014322757720947266, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4699, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:34:17'),
(889, 4, 1, 0.01147317886352539, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6896, \"connections\": 2}', '2025-07-07 16:34:17'),
(890, 5, 0, 0.014845, NULL, NULL, '2025-07-07 16:34:17'),
(891, 6, 1, 0.008336, NULL, NULL, '2025-07-07 16:34:17'),
(892, 7, 0, 0.0899040699005127, '', NULL, '2025-07-07 16:34:17'),
(893, 1, 1, 0.016229, NULL, NULL, '2025-07-07 16:34:23'),
(894, 2, 1, 0.002853870391845703, NULL, NULL, '2025-07-07 16:34:23'),
(895, 3, 1, 0.07068800926208496, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4705, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:34:23'),
(896, 4, 1, 0.01531529426574707, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6902, \"connections\": 2}', '2025-07-07 16:34:23'),
(897, 5, 0, 0.010811, NULL, NULL, '2025-07-07 16:34:23'),
(898, 6, 1, 0.006806, NULL, NULL, '2025-07-07 16:34:23'),
(899, 7, 0, 0.02593374252319336, '', NULL, '2025-07-07 16:34:23'),
(900, 1, 1, 0.024287, NULL, NULL, '2025-07-07 16:34:54'),
(901, 2, 1, 0.003954410552978516, NULL, NULL, '2025-07-07 16:34:54'),
(902, 3, 1, 0.024044036865234375, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4736, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:34:54'),
(903, 4, 1, 0.010159969329833984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6933, \"connections\": 2}', '2025-07-07 16:34:54'),
(904, 5, 0, 0.008298, NULL, NULL, '2025-07-07 16:34:54'),
(905, 6, 1, 0.011544, NULL, NULL, '2025-07-07 16:34:54'),
(906, 7, 0, 0.02954387664794922, '', NULL, '2025-07-07 16:34:54'),
(907, 1, 1, 0.022855, NULL, NULL, '2025-07-07 16:35:03'),
(908, 2, 1, 0.0007548332214355469, NULL, NULL, '2025-07-07 16:35:03'),
(909, 3, 1, 0.006212949752807617, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4746, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:04'),
(910, 4, 1, 0.005769968032836914, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6943, \"connections\": 2}', '2025-07-07 16:35:04'),
(911, 5, 0, 0.004343, NULL, NULL, '2025-07-07 16:35:04'),
(912, 6, 1, 0.005826, NULL, NULL, '2025-07-07 16:35:04'),
(913, 7, 0, 0.015341758728027344, '', NULL, '2025-07-07 16:35:04'),
(914, 1, 1, 0.011658, NULL, NULL, '2025-07-07 16:35:13'),
(915, 2, 1, 0.0005939006805419922, NULL, NULL, '2025-07-07 16:35:13'),
(916, 3, 1, 0.008643150329589844, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4756, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:14'),
(917, 4, 1, 0.003993988037109375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6953, \"connections\": 2}', '2025-07-07 16:35:14'),
(918, 5, 0, 0.003773, NULL, NULL, '2025-07-07 16:35:14'),
(919, 6, 1, 0.003841, NULL, NULL, '2025-07-07 16:35:14'),
(920, 7, 0, 0.008942842483520508, '', NULL, '2025-07-07 16:35:14'),
(921, 1, 1, 0.006137, NULL, NULL, '2025-07-07 16:35:23'),
(922, 2, 1, 0.0008540153503417969, NULL, NULL, '2025-07-07 16:35:23'),
(923, 3, 1, 0.009671211242675781, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4765, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:24');
INSERT INTO `service_logs` (`id`, `service_id`, `status`, `response_time`, `error_message`, `additional_data`, `checked_at`) VALUES
(924, 4, 1, 0.005970954895019531, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6963, \"connections\": 2}', '2025-07-07 16:35:24'),
(925, 5, 0, 0.00485, NULL, NULL, '2025-07-07 16:35:24'),
(926, 6, 1, 0.003635, NULL, NULL, '2025-07-07 16:35:24'),
(927, 7, 0, 0.005532026290893555, '', NULL, '2025-07-07 16:35:24'),
(928, 1, 1, 0.009196, NULL, NULL, '2025-07-07 16:35:33'),
(929, 2, 1, 0.0005660057067871094, NULL, NULL, '2025-07-07 16:35:33'),
(930, 3, 1, 0.010532140731811523, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4775, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:33'),
(931, 4, 1, 0.005082845687866211, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6973, \"connections\": 2}', '2025-07-07 16:35:34'),
(932, 5, 0, 0.004374, NULL, NULL, '2025-07-07 16:35:34'),
(933, 6, 1, 0.003682, NULL, NULL, '2025-07-07 16:35:34'),
(934, 7, 0, 0.008379936218261719, '', NULL, '2025-07-07 16:35:34'),
(935, 1, 1, 0.014237, NULL, NULL, '2025-07-07 16:35:43'),
(936, 2, 1, 0.0024650096893310547, NULL, NULL, '2025-07-07 16:35:43'),
(937, 3, 1, 0.0065228939056396484, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4785, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:44'),
(938, 4, 1, 0.0027158260345458984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6983, \"connections\": 2}', '2025-07-07 16:35:44'),
(939, 5, 0, 0.003312, NULL, NULL, '2025-07-07 16:35:44'),
(940, 6, 1, 0.003551, NULL, NULL, '2025-07-07 16:35:44'),
(941, 7, 0, 0.00873708724975586, '', NULL, '2025-07-07 16:35:44'),
(942, 1, 1, 0.029489, NULL, NULL, '2025-07-07 16:35:53'),
(943, 2, 1, 0.0015761852264404297, NULL, NULL, '2025-07-07 16:35:54'),
(944, 3, 1, 0.007810831069946289, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4795, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:35:54'),
(945, 4, 1, 0.0031707286834716797, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 6993, \"connections\": 2}', '2025-07-07 16:35:54'),
(946, 5, 0, 0.00639, NULL, NULL, '2025-07-07 16:35:54'),
(947, 6, 1, 0.008745, NULL, NULL, '2025-07-07 16:35:54'),
(948, 7, 0, 0.02350020408630371, '', NULL, '2025-07-07 16:35:54'),
(949, 1, 1, 0.009145, NULL, NULL, '2025-07-07 16:36:03'),
(950, 2, 1, 0.0008578300476074219, NULL, NULL, '2025-07-07 16:36:03'),
(951, 3, 1, 0.007600069046020508, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4805, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:36:03'),
(952, 4, 1, 0.0047948360443115234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7003, \"connections\": 2}', '2025-07-07 16:36:04'),
(953, 5, 0, 0.006521, NULL, NULL, '2025-07-07 16:36:04'),
(954, 6, 1, 0.003487, NULL, NULL, '2025-07-07 16:36:04'),
(955, 7, 0, 0.008587837219238281, '', NULL, '2025-07-07 16:36:04'),
(956, 1, 1, 0.012982, NULL, NULL, '2025-07-07 16:36:23'),
(957, 2, 1, 0.0017080307006835938, NULL, NULL, '2025-07-07 16:36:23'),
(958, 3, 1, 0.006989002227783203, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4825, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:36:23'),
(959, 4, 1, 0.006173849105834961, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7022, \"connections\": 2}', '2025-07-07 16:36:23'),
(960, 5, 0, 0.005005, NULL, NULL, '2025-07-07 16:36:23'),
(961, 6, 1, 0.008148, NULL, NULL, '2025-07-07 16:36:23'),
(962, 7, 0, 0.019471168518066406, '', NULL, '2025-07-07 16:36:23'),
(963, 1, 1, 0.013278, NULL, NULL, '2025-07-07 16:38:28'),
(964, 2, 1, 0.0017910003662109375, NULL, NULL, '2025-07-07 16:38:28'),
(965, 3, 1, 0.007965087890625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4950, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:38:28'),
(966, 4, 1, 0.004899024963378906, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7147, \"connections\": 2}', '2025-07-07 16:38:28'),
(967, 5, 0, 0.004784, NULL, NULL, '2025-07-07 16:38:28'),
(968, 6, 1, 0.004173, NULL, NULL, '2025-07-07 16:38:28'),
(969, 7, 0, 0.008784055709838867, '', NULL, '2025-07-07 16:38:28'),
(970, 1, 1, 0.011989, NULL, NULL, '2025-07-07 16:38:38'),
(971, 2, 1, 0.0005528926849365234, NULL, NULL, '2025-07-07 16:38:38'),
(972, 3, 1, 0.014050006866455078, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4960, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:38:38'),
(973, 4, 1, 0.012000799179077148, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7157, \"connections\": 2}', '2025-07-07 16:38:38'),
(974, 5, 0, 0.008133, NULL, NULL, '2025-07-07 16:38:38'),
(975, 6, 1, 0.004306, NULL, NULL, '2025-07-07 16:38:38'),
(976, 7, 0, 0.018299102783203125, '', NULL, '2025-07-07 16:38:38'),
(977, 1, 1, 0.014214, NULL, NULL, '2025-07-07 16:40:36'),
(978, 2, 1, 0.0005288124084472656, NULL, NULL, '2025-07-07 16:40:36'),
(979, 3, 1, 0.014058828353881836, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5078, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:40:36'),
(980, 4, 1, 0.007484912872314453, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7275, \"connections\": 2}', '2025-07-07 16:40:36'),
(981, 5, 0, 0.016735, NULL, NULL, '2025-07-07 16:40:36'),
(982, 6, 1, 0.011033, NULL, NULL, '2025-07-07 16:40:36'),
(983, 7, 0, 0.01565861701965332, '', NULL, '2025-07-07 16:40:36'),
(984, 1, 1, 0.013958, NULL, NULL, '2025-07-07 16:40:39'),
(985, 2, 1, 0.00102996826171875, NULL, NULL, '2025-07-07 16:40:39'),
(986, 3, 1, 0.010125875473022461, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5081, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:40:39'),
(987, 4, 1, 0.005860805511474609, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7278, \"connections\": 2}', '2025-07-07 16:40:39'),
(988, 5, 0, 0.0048, NULL, NULL, '2025-07-07 16:40:39'),
(989, 6, 1, 0.00557, NULL, NULL, '2025-07-07 16:40:39'),
(990, 7, 0, 0.009142875671386719, '', NULL, '2025-07-07 16:40:39'),
(991, 1, 1, 0.013338, NULL, NULL, '2025-07-07 16:40:48'),
(992, 2, 1, 0.0005500316619873047, NULL, NULL, '2025-07-07 16:40:48'),
(993, 3, 1, 0.008608102798461914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5090, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:40:48'),
(994, 4, 1, 0.005860090255737305, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7287, \"connections\": 2}', '2025-07-07 16:40:48'),
(995, 5, 0, 0.004021, NULL, NULL, '2025-07-07 16:40:48'),
(996, 6, 1, 0.006109, NULL, NULL, '2025-07-07 16:40:49'),
(997, 7, 0, 0.01337289810180664, '', NULL, '2025-07-07 16:40:49'),
(998, 1, 1, 0.010479, NULL, NULL, '2025-07-07 16:40:58'),
(999, 2, 1, 0.0006439685821533203, NULL, NULL, '2025-07-07 16:40:58'),
(1000, 3, 1, 0.00576472282409668, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5100, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:40:58'),
(1001, 4, 1, 0.003097057342529297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7297, \"connections\": 2}', '2025-07-07 16:40:58'),
(1002, 5, 0, 0.003319, NULL, NULL, '2025-07-07 16:40:58'),
(1003, 6, 1, 0.004131, NULL, NULL, '2025-07-07 16:40:58'),
(1004, 7, 0, 0.008100032806396484, '', NULL, '2025-07-07 16:40:58'),
(1005, 1, 1, 0.018134, NULL, NULL, '2025-07-07 16:41:09'),
(1006, 2, 1, 0.0009529590606689453, NULL, NULL, '2025-07-07 16:41:09'),
(1007, 3, 1, 0.01584005355834961, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5111, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:09'),
(1008, 4, 1, 0.008183717727661133, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7308, \"connections\": 2}', '2025-07-07 16:41:09'),
(1009, 5, 0, 0.008749, NULL, NULL, '2025-07-07 16:41:09'),
(1010, 6, 1, 0.006052, NULL, NULL, '2025-07-07 16:41:09'),
(1011, 7, 0, 0.10166788101196289, '', NULL, '2025-07-07 16:41:09'),
(1012, 1, 1, 0.020045, NULL, NULL, '2025-07-07 16:41:19'),
(1013, 2, 1, 0.0005083084106445312, NULL, NULL, '2025-07-07 16:41:19'),
(1014, 3, 1, 0.005584001541137695, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5121, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:19'),
(1015, 4, 1, 0.004616975784301758, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7318, \"connections\": 2}', '2025-07-07 16:41:19'),
(1016, 5, 0, 0.003879, NULL, NULL, '2025-07-07 16:41:19'),
(1017, 6, 1, 0.00363, NULL, NULL, '2025-07-07 16:41:19'),
(1018, 7, 0, 0.012607097625732422, '', NULL, '2025-07-07 16:41:19'),
(1019, 1, 1, 0.013815, NULL, NULL, '2025-07-07 16:41:28'),
(1020, 2, 1, 0.005033969879150391, NULL, NULL, '2025-07-07 16:41:28'),
(1021, 3, 1, 0.009206056594848633, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5130, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:28'),
(1022, 4, 1, 0.0032570362091064453, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7327, \"connections\": 2}', '2025-07-07 16:41:28'),
(1023, 5, 0, 0.004142, NULL, NULL, '2025-07-07 16:41:28'),
(1024, 6, 1, 0.003443, NULL, NULL, '2025-07-07 16:41:28'),
(1025, 7, 0, 0.008520841598510742, '', NULL, '2025-07-07 16:41:28'),
(1026, 1, 1, 0.021958, NULL, NULL, '2025-07-07 16:41:35'),
(1027, 2, 1, 0.01627182960510254, NULL, NULL, '2025-07-07 16:41:35'),
(1028, 3, 1, 0.016769886016845703, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5137, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:35'),
(1029, 4, 1, 0.00586700439453125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7334, \"connections\": 2}', '2025-07-07 16:41:35'),
(1030, 5, 0, 0.004084, NULL, NULL, '2025-07-07 16:41:35'),
(1031, 6, 1, 0.004613, NULL, NULL, '2025-07-07 16:41:35'),
(1032, 7, 0, 0.009268760681152344, '', NULL, '2025-07-07 16:41:35'),
(1033, 1, 1, 0.01289, NULL, NULL, '2025-07-07 16:41:45'),
(1034, 2, 1, 0.0007319450378417969, NULL, NULL, '2025-07-07 16:41:45'),
(1035, 3, 1, 0.01314687728881836, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5147, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:45'),
(1036, 4, 1, 0.004604816436767578, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7344, \"connections\": 2}', '2025-07-07 16:41:45'),
(1037, 5, 0, 0.006601, NULL, NULL, '2025-07-07 16:41:45'),
(1038, 6, 1, 0.00807, NULL, NULL, '2025-07-07 16:41:45'),
(1039, 7, 0, 0.014407873153686523, '', NULL, '2025-07-07 16:41:45'),
(1040, 1, 1, 0.081147, NULL, NULL, '2025-07-07 16:41:52'),
(1041, 2, 1, 0.005429983139038086, NULL, NULL, '2025-07-07 16:41:52'),
(1042, 3, 1, 0.019148826599121094, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5154, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:41:52'),
(1043, 4, 1, 0.0033164024353027344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7351, \"connections\": 2}', '2025-07-07 16:41:52'),
(1044, 5, 0, 0.011972, NULL, NULL, '2025-07-07 16:41:52'),
(1045, 6, 1, 0.008968, NULL, NULL, '2025-07-07 16:41:52'),
(1046, 7, 0, 0.017420053482055664, '', NULL, '2025-07-07 16:41:52'),
(1047, 1, 1, 0.013332, NULL, NULL, '2025-07-07 16:42:02'),
(1048, 2, 1, 0.00045990943908691406, NULL, NULL, '2025-07-07 16:42:02'),
(1049, 3, 1, 0.00571894645690918, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5164, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:02'),
(1050, 4, 1, 0.0032868385314941406, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7361, \"connections\": 2}', '2025-07-07 16:42:02'),
(1051, 5, 0, 0.004721, NULL, NULL, '2025-07-07 16:42:02'),
(1052, 6, 1, 0.003571, NULL, NULL, '2025-07-07 16:42:02'),
(1053, 7, 0, 0.0077991485595703125, '', NULL, '2025-07-07 16:42:02'),
(1054, 1, 1, 0.015361, NULL, NULL, '2025-07-07 16:42:12'),
(1055, 2, 1, 0.0015261173248291016, NULL, NULL, '2025-07-07 16:42:12'),
(1056, 3, 1, 0.0054891109466552734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5174, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:12'),
(1057, 4, 1, 0.003017902374267578, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7371, \"connections\": 2}', '2025-07-07 16:42:12'),
(1058, 5, 0, 0.004066, NULL, NULL, '2025-07-07 16:42:12'),
(1059, 6, 1, 0.003342, NULL, NULL, '2025-07-07 16:42:12'),
(1060, 7, 0, 0.008227109909057617, '', NULL, '2025-07-07 16:42:12'),
(1061, 1, 1, 0.015561, NULL, NULL, '2025-07-07 16:42:22'),
(1062, 2, 1, 0.001039266586303711, NULL, NULL, '2025-07-07 16:42:22'),
(1063, 3, 1, 0.005793094635009766, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5184, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:22'),
(1064, 4, 1, 0.0034532546997070312, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7381, \"connections\": 2}', '2025-07-07 16:42:22'),
(1065, 5, 0, 0.004172, NULL, NULL, '2025-07-07 16:42:22'),
(1066, 6, 1, 0.003331, NULL, NULL, '2025-07-07 16:42:22'),
(1067, 7, 0, 0.008095979690551758, '', NULL, '2025-07-07 16:42:22'),
(1068, 1, 1, 0.014646, NULL, NULL, '2025-07-07 16:42:32'),
(1069, 2, 1, 0.0005140304565429688, NULL, NULL, '2025-07-07 16:42:32'),
(1070, 3, 1, 0.00668787956237793, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5194, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:32'),
(1071, 4, 1, 0.0033757686614990234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7391, \"connections\": 2}', '2025-07-07 16:42:32'),
(1072, 5, 0, 0.004217, NULL, NULL, '2025-07-07 16:42:32'),
(1073, 6, 1, 0.00387, NULL, NULL, '2025-07-07 16:42:32'),
(1074, 7, 0, 0.008668899536132812, '', NULL, '2025-07-07 16:42:32'),
(1075, 1, 1, 0.014477, NULL, NULL, '2025-07-07 16:42:42'),
(1076, 2, 1, 0.00189971923828125, NULL, NULL, '2025-07-07 16:42:42'),
(1077, 3, 1, 0.006062984466552734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5204, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:42'),
(1078, 4, 1, 0.0028820037841796875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7401, \"connections\": 2}', '2025-07-07 16:42:42'),
(1079, 5, 0, 0.003875, NULL, NULL, '2025-07-07 16:42:42'),
(1080, 6, 1, 0.003633, NULL, NULL, '2025-07-07 16:42:42'),
(1081, 7, 0, 0.00802302360534668, '', NULL, '2025-07-07 16:42:42'),
(1082, 1, 1, 0.014631, NULL, NULL, '2025-07-07 16:42:52'),
(1083, 2, 1, 0.0008690357208251953, NULL, NULL, '2025-07-07 16:42:52'),
(1084, 3, 1, 0.005563974380493164, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5214, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:42:52'),
(1085, 4, 1, 0.0029611587524414062, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7411, \"connections\": 2}', '2025-07-07 16:42:52'),
(1086, 5, 0, 0.004626, NULL, NULL, '2025-07-07 16:42:52'),
(1087, 6, 1, 0.003527, NULL, NULL, '2025-07-07 16:42:52'),
(1088, 7, 0, 0.010815143585205078, '', NULL, '2025-07-07 16:42:52'),
(1089, 1, 1, 0.007455, NULL, NULL, '2025-07-07 16:43:02'),
(1090, 2, 1, 0.0005528926849365234, NULL, NULL, '2025-07-07 16:43:02'),
(1091, 3, 1, 0.008394002914428711, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5224, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:02'),
(1092, 4, 1, 0.0042188167572021484, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7421, \"connections\": 2}', '2025-07-07 16:43:02'),
(1093, 5, 0, 0.006745, NULL, NULL, '2025-07-07 16:43:02'),
(1094, 6, 1, 0.005207, NULL, NULL, '2025-07-07 16:43:02'),
(1095, 7, 0, 0.008468866348266602, '', NULL, '2025-07-07 16:43:02'),
(1096, 1, 1, 0.013467, NULL, NULL, '2025-07-07 16:43:12'),
(1097, 2, 1, 0.0009288787841796875, NULL, NULL, '2025-07-07 16:43:12'),
(1098, 3, 1, 0.0055119991302490234, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5234, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:12'),
(1099, 4, 1, 0.0028526782989501953, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7431, \"connections\": 2}', '2025-07-07 16:43:12'),
(1100, 5, 0, 0.003753, NULL, NULL, '2025-07-07 16:43:12'),
(1101, 6, 1, 0.003369, NULL, NULL, '2025-07-07 16:43:12'),
(1102, 7, 0, 0.008281946182250977, '', NULL, '2025-07-07 16:43:12'),
(1103, 1, 1, 0.013882, NULL, NULL, '2025-07-07 16:43:22'),
(1104, 2, 1, 0.0004489421844482422, NULL, NULL, '2025-07-07 16:43:22'),
(1105, 3, 1, 0.004825115203857422, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5244, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:22'),
(1106, 4, 1, 0.005819082260131836, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7441, \"connections\": 2}', '2025-07-07 16:43:22'),
(1107, 5, 0, 0.00484, NULL, NULL, '2025-07-07 16:43:22'),
(1108, 6, 1, 0.003682, NULL, NULL, '2025-07-07 16:43:22'),
(1109, 7, 0, 0.008509159088134766, '', NULL, '2025-07-07 16:43:22'),
(1110, 1, 1, 0.007522, NULL, NULL, '2025-07-07 16:43:32'),
(1111, 2, 1, 0.0008640289306640625, NULL, NULL, '2025-07-07 16:43:32'),
(1112, 3, 1, 0.010405778884887695, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5254, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:32'),
(1113, 4, 1, 0.003957986831665039, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7451, \"connections\": 2}', '2025-07-07 16:43:32'),
(1114, 5, 0, 0.003853, NULL, NULL, '2025-07-07 16:43:32'),
(1115, 6, 1, 0.007719, NULL, NULL, '2025-07-07 16:43:32'),
(1116, 7, 0, 0.006356954574584961, '', NULL, '2025-07-07 16:43:32'),
(1117, 1, 1, 0.013213, NULL, NULL, '2025-07-07 16:43:42'),
(1118, 2, 1, 0.0005328655242919922, NULL, NULL, '2025-07-07 16:43:42'),
(1119, 3, 1, 0.00570225715637207, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5264, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:42'),
(1120, 4, 1, 0.0028290748596191406, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7461, \"connections\": 2}', '2025-07-07 16:43:42'),
(1121, 5, 0, 0.003423, NULL, NULL, '2025-07-07 16:43:42'),
(1122, 6, 1, 0.004148, NULL, NULL, '2025-07-07 16:43:42'),
(1123, 7, 0, 0.00791621208190918, '', NULL, '2025-07-07 16:43:42'),
(1124, 1, 1, 0.009411, NULL, NULL, '2025-07-07 16:43:52'),
(1125, 2, 1, 0.0005397796630859375, NULL, NULL, '2025-07-07 16:43:52'),
(1126, 3, 1, 0.014819145202636719, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5274, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:43:52'),
(1127, 4, 1, 0.0027489662170410156, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7471, \"connections\": 2}', '2025-07-07 16:43:52'),
(1128, 5, 0, 0.005188, NULL, NULL, '2025-07-07 16:43:52'),
(1129, 6, 1, 0.005094, NULL, NULL, '2025-07-07 16:43:52'),
(1130, 7, 0, 0.008562803268432617, '', NULL, '2025-07-07 16:43:52'),
(1131, 1, 1, 0.006848, NULL, NULL, '2025-07-07 16:44:02'),
(1132, 2, 1, 0.0007150173187255859, NULL, NULL, '2025-07-07 16:44:02'),
(1133, 3, 1, 0.009987115859985352, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5284, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:02'),
(1134, 4, 1, 0.0034232139587402344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7481, \"connections\": 2}', '2025-07-07 16:44:02'),
(1135, 5, 0, 0.003568, NULL, NULL, '2025-07-07 16:44:02'),
(1136, 6, 1, 0.004422, NULL, NULL, '2025-07-07 16:44:02'),
(1137, 7, 0, 0.007766246795654297, '', NULL, '2025-07-07 16:44:02'),
(1138, 1, 1, 0.006509, NULL, NULL, '2025-07-07 16:44:12'),
(1139, 2, 1, 0.00086212158203125, NULL, NULL, '2025-07-07 16:44:12'),
(1140, 3, 1, 0.009435176849365234, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5294, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:12'),
(1141, 4, 1, 0.004729032516479492, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7491, \"connections\": 2}', '2025-07-07 16:44:12'),
(1142, 5, 0, 0.004617, NULL, NULL, '2025-07-07 16:44:12'),
(1143, 6, 1, 0.00448, NULL, NULL, '2025-07-07 16:44:12'),
(1144, 7, 0, 0.01607203483581543, '', NULL, '2025-07-07 16:44:12'),
(1145, 1, 1, 0.005797, NULL, NULL, '2025-07-07 16:44:22'),
(1146, 2, 1, 0.0007228851318359375, NULL, NULL, '2025-07-07 16:44:22'),
(1147, 3, 1, 0.009685993194580078, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5304, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:22'),
(1148, 4, 1, 0.0031838417053222656, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7501, \"connections\": 2}', '2025-07-07 16:44:22'),
(1149, 5, 0, 0.003347, NULL, NULL, '2025-07-07 16:44:22'),
(1150, 6, 1, 0.006444, NULL, NULL, '2025-07-07 16:44:22'),
(1151, 7, 0, 0.008782148361206055, '', NULL, '2025-07-07 16:44:22'),
(1152, 1, 1, 0.010576, NULL, NULL, '2025-07-07 16:44:32'),
(1153, 2, 1, 0.002398967742919922, NULL, NULL, '2025-07-07 16:44:32'),
(1154, 3, 1, 0.008502006530761719, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5314, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:32'),
(1155, 4, 1, 0.0040130615234375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7511, \"connections\": 2}', '2025-07-07 16:44:32'),
(1156, 5, 0, 0.004225, NULL, NULL, '2025-07-07 16:44:32'),
(1157, 6, 1, 0.003471, NULL, NULL, '2025-07-07 16:44:32'),
(1158, 7, 0, 0.007524013519287109, '', NULL, '2025-07-07 16:44:32'),
(1159, 1, 1, 0.007341, NULL, NULL, '2025-07-07 16:44:42'),
(1160, 2, 1, 0.0010519027709960938, NULL, NULL, '2025-07-07 16:44:42'),
(1161, 3, 1, 0.011330842971801758, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5324, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:42'),
(1162, 4, 1, 0.0028982162475585938, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7521, \"connections\": 2}', '2025-07-07 16:44:42'),
(1163, 5, 0, 0.003532, NULL, NULL, '2025-07-07 16:44:42'),
(1164, 6, 1, 0.003559, NULL, NULL, '2025-07-07 16:44:42'),
(1165, 7, 0, 0.010233163833618164, '', NULL, '2025-07-07 16:44:42'),
(1166, 1, 1, 0.010556, NULL, NULL, '2025-07-07 16:44:52'),
(1167, 2, 1, 0.0007398128509521484, NULL, NULL, '2025-07-07 16:44:52'),
(1168, 3, 1, 0.00954294204711914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5334, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:44:52'),
(1169, 4, 1, 0.0035910606384277344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7531, \"connections\": 2}', '2025-07-07 16:44:52'),
(1170, 5, 0, 0.009321, NULL, NULL, '2025-07-07 16:44:52'),
(1171, 6, 1, 0.004052, NULL, NULL, '2025-07-07 16:44:52'),
(1172, 7, 0, 0.01404118537902832, '', NULL, '2025-07-07 16:44:52'),
(1173, 1, 1, 0.010503, NULL, NULL, '2025-07-07 16:45:02'),
(1174, 2, 1, 0.0005359649658203125, NULL, NULL, '2025-07-07 16:45:02'),
(1175, 3, 1, 0.009278059005737305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5344, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:02'),
(1176, 4, 1, 0.004063844680786133, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7541, \"connections\": 2}', '2025-07-07 16:45:02'),
(1177, 5, 0, 0.003942, NULL, NULL, '2025-07-07 16:45:02'),
(1178, 6, 1, 0.003644, NULL, NULL, '2025-07-07 16:45:02'),
(1179, 7, 0, 0.013769149780273438, '', NULL, '2025-07-07 16:45:02'),
(1180, 1, 1, 0.010766, NULL, NULL, '2025-07-07 16:45:12'),
(1181, 2, 1, 0.0014972686767578125, NULL, NULL, '2025-07-07 16:45:12'),
(1182, 3, 1, 0.008823871612548828, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5354, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:12'),
(1183, 4, 1, 0.0042476654052734375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7551, \"connections\": 2}', '2025-07-07 16:45:12'),
(1184, 5, 0, 0.004085, NULL, NULL, '2025-07-07 16:45:12'),
(1185, 6, 1, 0.004277, NULL, NULL, '2025-07-07 16:45:12'),
(1186, 7, 0, 0.007756233215332031, '', NULL, '2025-07-07 16:45:12'),
(1187, 1, 1, 0.012222, NULL, NULL, '2025-07-07 16:45:22'),
(1188, 2, 1, 0.0005388259887695312, NULL, NULL, '2025-07-07 16:45:22'),
(1189, 3, 1, 0.00833892822265625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5364, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:22'),
(1190, 4, 1, 0.0035309791564941406, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7561, \"connections\": 2}', '2025-07-07 16:45:22'),
(1191, 5, 0, 0.004482, NULL, NULL, '2025-07-07 16:45:22'),
(1192, 6, 1, 0.004091, NULL, NULL, '2025-07-07 16:45:22'),
(1193, 7, 0, 0.00783991813659668, '', NULL, '2025-07-07 16:45:22'),
(1194, 1, 1, 0.017169, NULL, NULL, '2025-07-07 16:45:32'),
(1195, 2, 1, 0.0016760826110839844, NULL, NULL, '2025-07-07 16:45:32'),
(1196, 3, 1, 0.008810043334960938, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5374, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:32'),
(1197, 4, 1, 0.007272005081176758, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7571, \"connections\": 2}', '2025-07-07 16:45:32'),
(1198, 5, 0, 0.005316, NULL, NULL, '2025-07-07 16:45:32'),
(1199, 6, 1, 0.005255, NULL, NULL, '2025-07-07 16:45:32'),
(1200, 7, 0, 0.015150785446166992, '', NULL, '2025-07-07 16:45:32'),
(1201, 1, 1, 0.012826, NULL, NULL, '2025-07-07 16:45:42'),
(1202, 2, 1, 0.0020198822021484375, NULL, NULL, '2025-07-07 16:45:42'),
(1203, 3, 1, 0.009369134902954102, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5384, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:42'),
(1204, 4, 1, 0.0033109188079833984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7581, \"connections\": 2}', '2025-07-07 16:45:42'),
(1205, 5, 0, 0.007123, NULL, NULL, '2025-07-07 16:45:42'),
(1206, 6, 1, 0.006163, NULL, NULL, '2025-07-07 16:45:42'),
(1207, 7, 0, 0.015558958053588867, '', NULL, '2025-07-07 16:45:42'),
(1208, 1, 1, 0.018097, NULL, NULL, '2025-07-07 16:45:52'),
(1209, 2, 1, 0.0009579658508300781, NULL, NULL, '2025-07-07 16:45:52'),
(1210, 3, 1, 0.008764982223510742, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5394, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:45:52'),
(1211, 4, 1, 0.003985881805419922, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7591, \"connections\": 2}', '2025-07-07 16:45:52'),
(1212, 5, 0, 0.005316, NULL, NULL, '2025-07-07 16:45:52'),
(1213, 6, 1, 0.003737, NULL, NULL, '2025-07-07 16:45:52'),
(1214, 7, 0, 0.009998083114624023, '', NULL, '2025-07-07 16:45:52'),
(1215, 1, 1, 0.010742, NULL, NULL, '2025-07-07 16:46:02'),
(1216, 2, 1, 0.001878976821899414, NULL, NULL, '2025-07-07 16:46:02'),
(1217, 3, 1, 0.011792898178100586, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5404, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:02'),
(1218, 4, 1, 0.003922939300537109, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7601, \"connections\": 2}', '2025-07-07 16:46:02'),
(1219, 5, 0, 0.007055, NULL, NULL, '2025-07-07 16:46:02'),
(1220, 6, 1, 0.004055, NULL, NULL, '2025-07-07 16:46:02'),
(1221, 7, 0, 0.012475252151489258, '', NULL, '2025-07-07 16:46:02'),
(1222, 1, 1, 0.012659, NULL, NULL, '2025-07-07 16:46:12'),
(1223, 2, 1, 0.0004899501800537109, NULL, NULL, '2025-07-07 16:46:12'),
(1224, 3, 1, 0.008395910263061523, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5414, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:12'),
(1225, 4, 1, 0.0027451515197753906, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7611, \"connections\": 2}', '2025-07-07 16:46:12'),
(1226, 5, 0, 0.005145, NULL, NULL, '2025-07-07 16:46:12'),
(1227, 6, 1, 0.003686, NULL, NULL, '2025-07-07 16:46:12'),
(1228, 7, 0, 0.01011514663696289, '', NULL, '2025-07-07 16:46:12'),
(1229, 1, 1, 0.014568, NULL, NULL, '2025-07-07 16:46:22'),
(1230, 2, 1, 0.0008172988891601562, NULL, NULL, '2025-07-07 16:46:22'),
(1231, 3, 1, 0.008734941482543945, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5424, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:22'),
(1232, 4, 1, 0.004237651824951172, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7621, \"connections\": 2}', '2025-07-07 16:46:22'),
(1233, 5, 0, 0.00354, NULL, NULL, '2025-07-07 16:46:22'),
(1234, 6, 1, 0.004864, NULL, NULL, '2025-07-07 16:46:22'),
(1235, 7, 0, 0.014271259307861328, '', NULL, '2025-07-07 16:46:22'),
(1236, 1, 1, 0.013474, NULL, NULL, '2025-07-07 16:46:32'),
(1237, 2, 1, 0.004644155502319336, NULL, NULL, '2025-07-07 16:46:32'),
(1238, 3, 1, 0.005541086196899414, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5434, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:32'),
(1239, 4, 1, 0.0027718544006347656, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7631, \"connections\": 2}', '2025-07-07 16:46:32'),
(1240, 5, 0, 0.018564, NULL, NULL, '2025-07-07 16:46:32'),
(1241, 6, 1, 0.003445, NULL, NULL, '2025-07-07 16:46:32'),
(1242, 7, 0, 0.008489131927490234, '', NULL, '2025-07-07 16:46:32'),
(1243, 1, 1, 0.01284, NULL, NULL, '2025-07-07 16:46:42'),
(1244, 2, 1, 0.0006258487701416016, NULL, NULL, '2025-07-07 16:46:42'),
(1245, 3, 1, 0.0075762271881103516, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5444, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:42'),
(1246, 4, 1, 0.0027618408203125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7641, \"connections\": 2}', '2025-07-07 16:46:42'),
(1247, 5, 0, 0.008361, NULL, NULL, '2025-07-07 16:46:42'),
(1248, 6, 1, 0.005696, NULL, NULL, '2025-07-07 16:46:42'),
(1249, 7, 0, 0.005819797515869141, '', NULL, '2025-07-07 16:46:42'),
(1250, 1, 1, 0.010646, NULL, NULL, '2025-07-07 16:46:52'),
(1251, 2, 1, 0.0009379386901855469, NULL, NULL, '2025-07-07 16:46:52'),
(1252, 3, 1, 0.009518861770629883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5454, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:46:52'),
(1253, 4, 1, 0.0029141902923583984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7651, \"connections\": 2}', '2025-07-07 16:46:52'),
(1254, 5, 0, 0.006766, NULL, NULL, '2025-07-07 16:46:52'),
(1255, 6, 1, 0.005027, NULL, NULL, '2025-07-07 16:46:52'),
(1256, 7, 0, 0.00564885139465332, '', NULL, '2025-07-07 16:46:52'),
(1257, 1, 1, 0.012901, NULL, NULL, '2025-07-07 16:47:02'),
(1258, 2, 1, 0.0005140304565429688, NULL, NULL, '2025-07-07 16:47:02'),
(1259, 3, 1, 0.011513948440551758, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5464, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:02'),
(1260, 4, 1, 0.011931896209716797, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7661, \"connections\": 2}', '2025-07-07 16:47:02'),
(1261, 5, 0, 0.008439, NULL, NULL, '2025-07-07 16:47:02'),
(1262, 6, 1, 0.010481, NULL, NULL, '2025-07-07 16:47:02'),
(1263, 7, 0, 0.01690959930419922, '', NULL, '2025-07-07 16:47:02'),
(1264, 1, 1, 0.017684, NULL, NULL, '2025-07-07 16:47:12'),
(1265, 2, 1, 0.0006649494171142578, NULL, NULL, '2025-07-07 16:47:12'),
(1266, 3, 1, 0.011652708053588867, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5474, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:12'),
(1267, 4, 1, 0.006240129470825195, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7671, \"connections\": 2}', '2025-07-07 16:47:12'),
(1268, 5, 0, 0.005144, NULL, NULL, '2025-07-07 16:47:12'),
(1269, 6, 1, 0.004061, NULL, NULL, '2025-07-07 16:47:12'),
(1270, 7, 0, 0.015413999557495117, '', NULL, '2025-07-07 16:47:12'),
(1271, 1, 1, 0.011172, NULL, NULL, '2025-07-07 16:47:22'),
(1272, 2, 1, 0.0007586479187011719, NULL, NULL, '2025-07-07 16:47:22'),
(1273, 3, 1, 0.0069921016693115234, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5484, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:22'),
(1274, 4, 1, 0.004071712493896484, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7681, \"connections\": 2}', '2025-07-07 16:47:22'),
(1275, 5, 0, 0.006257, NULL, NULL, '2025-07-07 16:47:22'),
(1276, 6, 1, 0.005101, NULL, NULL, '2025-07-07 16:47:22'),
(1277, 7, 0, 0.007627010345458984, '', NULL, '2025-07-07 16:47:22'),
(1278, 1, 1, 0.010344, NULL, NULL, '2025-07-07 16:47:32'),
(1279, 2, 1, 0.0013942718505859375, NULL, NULL, '2025-07-07 16:47:32'),
(1280, 3, 1, 0.007435798645019531, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5494, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:32'),
(1281, 4, 1, 0.005948305130004883, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7691, \"connections\": 2}', '2025-07-07 16:47:32'),
(1282, 5, 0, 0.004237, NULL, NULL, '2025-07-07 16:47:32'),
(1283, 6, 1, 0.004139, NULL, NULL, '2025-07-07 16:47:32'),
(1284, 7, 0, 0.008020877838134766, '', NULL, '2025-07-07 16:47:32'),
(1285, 1, 1, 0.011352, NULL, NULL, '2025-07-07 16:47:42'),
(1286, 2, 1, 0.0005099773406982422, NULL, NULL, '2025-07-07 16:47:42'),
(1287, 3, 1, 0.008279085159301758, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5504, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:42'),
(1288, 4, 1, 0.003099203109741211, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7701, \"connections\": 2}', '2025-07-07 16:47:42'),
(1289, 5, 0, 0.008195, NULL, NULL, '2025-07-07 16:47:42'),
(1290, 6, 1, 0.005775, NULL, NULL, '2025-07-07 16:47:42'),
(1291, 7, 0, 0.005553245544433594, '', NULL, '2025-07-07 16:47:42'),
(1292, 1, 1, 0.013852, NULL, NULL, '2025-07-07 16:47:52'),
(1293, 2, 1, 0.003654956817626953, NULL, NULL, '2025-07-07 16:47:52'),
(1294, 3, 1, 0.007909774780273438, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5514, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:47:52'),
(1295, 4, 1, 0.003225088119506836, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7711, \"connections\": 2}', '2025-07-07 16:47:52'),
(1296, 5, 0, 0.005175, NULL, NULL, '2025-07-07 16:47:52'),
(1297, 6, 1, 0.005205, NULL, NULL, '2025-07-07 16:47:52'),
(1298, 7, 0, 0.007009029388427734, '', NULL, '2025-07-07 16:47:52'),
(1299, 1, 1, 0.013079, NULL, NULL, '2025-07-07 16:48:02'),
(1300, 2, 1, 0.0006310939788818359, NULL, NULL, '2025-07-07 16:48:02'),
(1301, 3, 1, 0.00914621353149414, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5524, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:02'),
(1302, 4, 1, 0.0034172534942626953, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7721, \"connections\": 2}', '2025-07-07 16:48:02'),
(1303, 5, 0, 0.005423, NULL, NULL, '2025-07-07 16:48:02'),
(1304, 6, 1, 0.004433, NULL, NULL, '2025-07-07 16:48:02'),
(1305, 7, 0, 0.008506059646606445, '', NULL, '2025-07-07 16:48:02'),
(1306, 1, 1, 0.012971, NULL, NULL, '2025-07-07 16:48:12'),
(1307, 2, 1, 0.0005979537963867188, NULL, NULL, '2025-07-07 16:48:12'),
(1308, 3, 1, 0.008393049240112305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5534, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:12'),
(1309, 4, 1, 0.0029790401458740234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7731, \"connections\": 2}', '2025-07-07 16:48:12'),
(1310, 5, 0, 0.005862, NULL, NULL, '2025-07-07 16:48:12'),
(1311, 6, 1, 0.004609, NULL, NULL, '2025-07-07 16:48:12'),
(1312, 7, 0, 0.00789189338684082, '', NULL, '2025-07-07 16:48:12'),
(1313, 1, 1, 0.014524, NULL, NULL, '2025-07-07 16:48:22'),
(1314, 2, 1, 0.003396749496459961, NULL, NULL, '2025-07-07 16:48:22'),
(1315, 3, 1, 0.010039091110229492, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5544, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:22'),
(1316, 4, 1, 0.0032219886779785156, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7741, \"connections\": 2}', '2025-07-07 16:48:22'),
(1317, 5, 0, 0.003217, NULL, NULL, '2025-07-07 16:48:22'),
(1318, 6, 1, 0.003774, NULL, NULL, '2025-07-07 16:48:22'),
(1319, 7, 0, 0.008491039276123047, '', NULL, '2025-07-07 16:48:22'),
(1320, 1, 1, 0.01398, NULL, NULL, '2025-07-07 16:48:32'),
(1321, 2, 1, 0.0009968280792236328, NULL, NULL, '2025-07-07 16:48:32'),
(1322, 3, 1, 0.011044025421142578, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5554, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:32'),
(1323, 4, 1, 0.008183956146240234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7751, \"connections\": 2}', '2025-07-07 16:48:32'),
(1324, 5, 0, 0.003749, NULL, NULL, '2025-07-07 16:48:32'),
(1325, 6, 1, 0.004244, NULL, NULL, '2025-07-07 16:48:32'),
(1326, 7, 0, 0.012722015380859375, '', NULL, '2025-07-07 16:48:32'),
(1327, 1, 1, 0.014676, NULL, NULL, '2025-07-07 16:48:42'),
(1328, 2, 1, 0.004521846771240234, NULL, NULL, '2025-07-07 16:48:42'),
(1329, 3, 1, 0.008529901504516602, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5564, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:42'),
(1330, 4, 1, 0.003341197967529297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7761, \"connections\": 2}', '2025-07-07 16:48:42'),
(1331, 5, 0, 0.003381, NULL, NULL, '2025-07-07 16:48:42'),
(1332, 6, 1, 0.003908, NULL, NULL, '2025-07-07 16:48:42'),
(1333, 7, 0, 0.008389949798583984, '', NULL, '2025-07-07 16:48:42'),
(1334, 1, 1, 0.017307, NULL, NULL, '2025-07-07 16:48:52'),
(1335, 2, 1, 0.0007770061492919922, NULL, NULL, '2025-07-07 16:48:52'),
(1336, 3, 1, 0.009411096572875977, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5574, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:48:52'),
(1337, 4, 1, 0.006506443023681641, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7771, \"connections\": 2}', '2025-07-07 16:48:52'),
(1338, 5, 0, 0.004854, NULL, NULL, '2025-07-07 16:48:52'),
(1339, 6, 1, 0.004006, NULL, NULL, '2025-07-07 16:48:52'),
(1340, 7, 0, 0.008110761642456055, '', NULL, '2025-07-07 16:48:52'),
(1341, 1, 1, 0.014044, NULL, NULL, '2025-07-07 16:49:02'),
(1342, 2, 1, 0.0006210803985595703, NULL, NULL, '2025-07-07 16:49:02'),
(1343, 3, 1, 0.00821995735168457, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5584, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:02'),
(1344, 4, 1, 0.0036439895629882812, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7781, \"connections\": 2}', '2025-07-07 16:49:02'),
(1345, 5, 0, 0.006519, NULL, NULL, '2025-07-07 16:49:02'),
(1346, 6, 1, 0.005191, NULL, NULL, '2025-07-07 16:49:02'),
(1347, 7, 0, 0.005761146545410156, '', NULL, '2025-07-07 16:49:02'),
(1348, 1, 1, 0.012408, NULL, NULL, '2025-07-07 16:49:12'),
(1349, 2, 1, 0.0049419403076171875, NULL, NULL, '2025-07-07 16:49:12'),
(1350, 3, 1, 0.008238077163696289, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5594, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:12'),
(1351, 4, 1, 0.003337860107421875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7791, \"connections\": 2}', '2025-07-07 16:49:12'),
(1352, 5, 0, 0.005213, NULL, NULL, '2025-07-07 16:49:12'),
(1353, 6, 1, 0.004459, NULL, NULL, '2025-07-07 16:49:12'),
(1354, 7, 0, 0.008053302764892578, '', NULL, '2025-07-07 16:49:12'),
(1355, 1, 1, 0.0124, NULL, NULL, '2025-07-07 16:49:22'),
(1356, 2, 1, 0.004439115524291992, NULL, NULL, '2025-07-07 16:49:22'),
(1357, 3, 1, 0.0076141357421875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5604, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:22'),
(1358, 4, 1, 0.0034160614013671875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7801, \"connections\": 2}', '2025-07-07 16:49:22'),
(1359, 5, 0, 0.005013, NULL, NULL, '2025-07-07 16:49:22'),
(1360, 6, 1, 0.004509, NULL, NULL, '2025-07-07 16:49:22'),
(1361, 7, 0, 0.0060846805572509766, '', NULL, '2025-07-07 16:49:22'),
(1362, 1, 1, 0.012631, NULL, NULL, '2025-07-07 16:49:32'),
(1363, 2, 1, 0.0005970001220703125, NULL, NULL, '2025-07-07 16:49:32'),
(1364, 3, 1, 0.009052038192749023, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5614, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:32'),
(1365, 4, 1, 0.003833293914794922, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7811, \"connections\": 2}', '2025-07-07 16:49:32'),
(1366, 5, 0, 0.004268, NULL, NULL, '2025-07-07 16:49:32'),
(1367, 6, 1, 0.003831, NULL, NULL, '2025-07-07 16:49:32'),
(1368, 7, 0, 0.008282899856567383, '', NULL, '2025-07-07 16:49:32'),
(1369, 1, 1, 0.012944, NULL, NULL, '2025-07-07 16:49:42'),
(1370, 2, 1, 0.0022106170654296875, NULL, NULL, '2025-07-07 16:49:42'),
(1371, 3, 1, 0.009017229080200195, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5624, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:42'),
(1372, 4, 1, 0.0034198760986328125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7821, \"connections\": 2}', '2025-07-07 16:49:42'),
(1373, 5, 0, 0.004963, NULL, NULL, '2025-07-07 16:49:42'),
(1374, 6, 1, 0.004431, NULL, NULL, '2025-07-07 16:49:42'),
(1375, 7, 0, 0.008507966995239258, '', NULL, '2025-07-07 16:49:42'),
(1376, 1, 1, 0.011793, NULL, NULL, '2025-07-07 16:49:52'),
(1377, 2, 1, 0.0024378299713134766, NULL, NULL, '2025-07-07 16:49:52'),
(1378, 3, 1, 0.007992982864379883, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5634, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:49:52'),
(1379, 4, 1, 0.002749919891357422, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7831, \"connections\": 2}', '2025-07-07 16:49:52'),
(1380, 5, 0, 0.008035, NULL, NULL, '2025-07-07 16:49:52'),
(1381, 6, 1, 0.00574, NULL, NULL, '2025-07-07 16:49:52'),
(1382, 7, 0, 0.00629878044128418, '', NULL, '2025-07-07 16:49:52'),
(1383, 1, 1, 0.011702, NULL, NULL, '2025-07-07 16:50:02'),
(1384, 2, 1, 0.0014879703521728516, NULL, NULL, '2025-07-07 16:50:02'),
(1385, 3, 1, 0.008687257766723633, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5644, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:02'),
(1386, 4, 1, 0.0037398338317871094, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7841, \"connections\": 2}', '2025-07-07 16:50:02'),
(1387, 5, 0, 0.003338, NULL, NULL, '2025-07-07 16:50:02'),
(1388, 6, 1, 0.00474, NULL, NULL, '2025-07-07 16:50:02'),
(1389, 7, 0, 0.008640050888061523, '', NULL, '2025-07-07 16:50:02'),
(1390, 1, 1, 0.011585, NULL, NULL, '2025-07-07 16:50:12'),
(1391, 2, 1, 0.0006608963012695312, NULL, NULL, '2025-07-07 16:50:12'),
(1392, 3, 1, 0.008615255355834961, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5654, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:12'),
(1393, 4, 1, 0.0029239654541015625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7851, \"connections\": 2}', '2025-07-07 16:50:12'),
(1394, 5, 0, 0.006492, NULL, NULL, '2025-07-07 16:50:12'),
(1395, 6, 1, 0.004569, NULL, NULL, '2025-07-07 16:50:12'),
(1396, 7, 0, 0.006840944290161133, '', NULL, '2025-07-07 16:50:12'),
(1397, 1, 1, 0.011523, NULL, NULL, '2025-07-07 16:50:22'),
(1398, 2, 1, 0.0021088123321533203, NULL, NULL, '2025-07-07 16:50:22'),
(1399, 3, 1, 0.008139848709106445, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5664, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:22'),
(1400, 4, 1, 0.0028951168060302734, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7861, \"connections\": 2}', '2025-07-07 16:50:22'),
(1401, 5, 0, 0.007757, NULL, NULL, '2025-07-07 16:50:22'),
(1402, 6, 1, 0.005916, NULL, NULL, '2025-07-07 16:50:22'),
(1403, 7, 0, 0.0080718994140625, '', NULL, '2025-07-07 16:50:22'),
(1404, 1, 1, 0.007599, NULL, NULL, '2025-07-07 16:50:32'),
(1405, 2, 1, 0.003993034362792969, NULL, NULL, '2025-07-07 16:50:32'),
(1406, 3, 1, 0.0064508914947509766, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5674, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:32'),
(1407, 4, 1, 0.0033288002014160156, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7871, \"connections\": 2}', '2025-07-07 16:50:32'),
(1408, 5, 0, 0.003792, NULL, NULL, '2025-07-07 16:50:32'),
(1409, 6, 1, 0.005464, NULL, NULL, '2025-07-07 16:50:32'),
(1410, 7, 0, 0.009340047836303711, '', NULL, '2025-07-07 16:50:32'),
(1411, 1, 1, 0.013595, NULL, NULL, '2025-07-07 16:50:42'),
(1412, 2, 1, 0.0006041526794433594, NULL, NULL, '2025-07-07 16:50:42'),
(1413, 3, 1, 0.008615970611572266, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5684, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:42'),
(1414, 4, 1, 0.004332780838012695, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7881, \"connections\": 2}', '2025-07-07 16:50:42'),
(1415, 5, 0, 0.003479, NULL, NULL, '2025-07-07 16:50:42'),
(1416, 6, 1, 0.00421, NULL, NULL, '2025-07-07 16:50:42'),
(1417, 7, 0, 0.00861215591430664, '', NULL, '2025-07-07 16:50:42'),
(1418, 1, 1, 0.014641, NULL, NULL, '2025-07-07 16:50:52'),
(1419, 2, 1, 0.0007600784301757812, NULL, NULL, '2025-07-07 16:50:52'),
(1420, 3, 1, 0.009769916534423828, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5694, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:50:52'),
(1421, 4, 1, 0.00621795654296875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7891, \"connections\": 2}', '2025-07-07 16:50:52'),
(1422, 5, 0, 0.004832, NULL, NULL, '2025-07-07 16:50:52'),
(1423, 6, 1, 0.003486, NULL, NULL, '2025-07-07 16:50:52'),
(1424, 7, 0, 0.01139378547668457, '', NULL, '2025-07-07 16:50:52'),
(1425, 1, 1, 0.012606, NULL, NULL, '2025-07-07 16:51:02'),
(1426, 2, 1, 0.0008680820465087891, NULL, NULL, '2025-07-07 16:51:02'),
(1427, 3, 1, 0.009034156799316406, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5704, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:02'),
(1428, 4, 1, 0.0035250186920166016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7901, \"connections\": 2}', '2025-07-07 16:51:02'),
(1429, 5, 0, 0.003424, NULL, NULL, '2025-07-07 16:51:02'),
(1430, 6, 1, 0.004367, NULL, NULL, '2025-07-07 16:51:02'),
(1431, 7, 0, 0.009359121322631836, '', NULL, '2025-07-07 16:51:02'),
(1432, 1, 1, 0.013325, NULL, NULL, '2025-07-07 16:51:12'),
(1433, 2, 1, 0.0008587837219238281, NULL, NULL, '2025-07-07 16:51:12'),
(1434, 3, 1, 0.008218765258789062, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5714, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:12'),
(1435, 4, 1, 0.0031168460845947266, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7911, \"connections\": 2}', '2025-07-07 16:51:12'),
(1436, 5, 0, 0.004316, NULL, NULL, '2025-07-07 16:51:12'),
(1437, 6, 1, 0.003665, NULL, NULL, '2025-07-07 16:51:12'),
(1438, 7, 0, 0.005385875701904297, '', NULL, '2025-07-07 16:51:12'),
(1439, 1, 1, 0.013599, NULL, NULL, '2025-07-07 16:51:22'),
(1440, 2, 1, 0.0007350444793701172, NULL, NULL, '2025-07-07 16:51:22'),
(1441, 3, 1, 0.009808778762817383, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5724, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:22'),
(1442, 4, 1, 0.006966114044189453, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7921, \"connections\": 2}', '2025-07-07 16:51:22'),
(1443, 5, 0, 0.005621, NULL, NULL, '2025-07-07 16:51:22'),
(1444, 6, 1, 0.00373, NULL, NULL, '2025-07-07 16:51:22'),
(1445, 7, 0, 0.011851072311401367, '', NULL, '2025-07-07 16:51:22'),
(1446, 1, 1, 0.012391, NULL, NULL, '2025-07-07 16:51:32'),
(1447, 2, 1, 0.0007338523864746094, NULL, NULL, '2025-07-07 16:51:32'),
(1448, 3, 1, 0.009535074234008789, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5734, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:32'),
(1449, 4, 1, 0.0031709671020507812, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7931, \"connections\": 2}', '2025-07-07 16:51:32'),
(1450, 5, 0, 0.005137, NULL, NULL, '2025-07-07 16:51:32'),
(1451, 6, 1, 0.004183, NULL, NULL, '2025-07-07 16:51:32'),
(1452, 7, 0, 0.0053141117095947266, '', NULL, '2025-07-07 16:51:32'),
(1453, 1, 1, 0.012704, NULL, NULL, '2025-07-07 16:51:42'),
(1454, 2, 1, 0.0005669593811035156, NULL, NULL, '2025-07-07 16:51:42'),
(1455, 3, 1, 0.011880874633789062, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5744, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:42'),
(1456, 4, 1, 0.004328012466430664, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7941, \"connections\": 2}', '2025-07-07 16:51:42'),
(1457, 5, 0, 0.005935, NULL, NULL, '2025-07-07 16:51:42'),
(1458, 6, 1, 0.003755, NULL, NULL, '2025-07-07 16:51:42'),
(1459, 7, 0, 0.009863138198852539, '', NULL, '2025-07-07 16:51:42'),
(1460, 1, 1, 0.014215, NULL, NULL, '2025-07-07 16:51:52'),
(1461, 2, 1, 0.0029451847076416016, NULL, NULL, '2025-07-07 16:51:52'),
(1462, 3, 1, 0.005752086639404297, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5754, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:51:52'),
(1463, 4, 1, 0.003248929977416992, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7951, \"connections\": 2}', '2025-07-07 16:51:52'),
(1464, 5, 0, 0.004571, NULL, NULL, '2025-07-07 16:51:52'),
(1465, 6, 1, 0.003593, NULL, NULL, '2025-07-07 16:51:52'),
(1466, 7, 0, 0.00934600830078125, '', NULL, '2025-07-07 16:51:52'),
(1467, 1, 1, 0.012406, NULL, NULL, '2025-07-07 16:52:02'),
(1468, 2, 1, 0.00046944618225097656, NULL, NULL, '2025-07-07 16:52:02'),
(1469, 3, 1, 0.009356975555419922, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5764, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:02'),
(1470, 4, 1, 0.004418849945068359, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7961, \"connections\": 2}', '2025-07-07 16:52:02'),
(1471, 5, 0, 0.004125, NULL, NULL, '2025-07-07 16:52:02'),
(1472, 6, 1, 0.003989, NULL, NULL, '2025-07-07 16:52:02'),
(1473, 7, 0, 0.008234977722167969, '', NULL, '2025-07-07 16:52:02'),
(1474, 1, 1, 0.012312, NULL, NULL, '2025-07-07 16:52:12'),
(1475, 2, 1, 0.0010230541229248047, NULL, NULL, '2025-07-07 16:52:12'),
(1476, 3, 1, 0.008070945739746094, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5774, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:12'),
(1477, 4, 1, 0.0034780502319335938, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7971, \"connections\": 2}', '2025-07-07 16:52:12'),
(1478, 5, 0, 0.005176, NULL, NULL, '2025-07-07 16:52:12'),
(1479, 6, 1, 0.003696, NULL, NULL, '2025-07-07 16:52:12'),
(1480, 7, 0, 0.007857084274291992, '', NULL, '2025-07-07 16:52:12'),
(1481, 1, 1, 0.011151, NULL, NULL, '2025-07-07 16:52:22'),
(1482, 2, 1, 0.0007331371307373047, NULL, NULL, '2025-07-07 16:52:22'),
(1483, 3, 1, 0.008201122283935547, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5784, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:22'),
(1484, 4, 1, 0.0032608509063720703, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7981, \"connections\": 2}', '2025-07-07 16:52:22'),
(1485, 5, 0, 0.005499, NULL, NULL, '2025-07-07 16:52:22'),
(1486, 6, 1, 0.005177, NULL, NULL, '2025-07-07 16:52:22'),
(1487, 7, 0, 0.0067331790924072266, '', NULL, '2025-07-07 16:52:22'),
(1488, 1, 1, 0.012632, NULL, NULL, '2025-07-07 16:52:32'),
(1489, 2, 1, 0.0006880760192871094, NULL, NULL, '2025-07-07 16:52:32'),
(1490, 3, 1, 0.007725954055786133, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5794, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:32'),
(1491, 4, 1, 0.0030670166015625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 7991, \"connections\": 2}', '2025-07-07 16:52:32'),
(1492, 5, 0, 0.004252, NULL, NULL, '2025-07-07 16:52:32'),
(1493, 6, 1, 0.003739, NULL, NULL, '2025-07-07 16:52:32'),
(1494, 7, 0, 0.00860905647277832, '', NULL, '2025-07-07 16:52:32'),
(1495, 1, 1, 0.014454, NULL, NULL, '2025-07-07 16:52:42'),
(1496, 2, 1, 0.0009388923645019531, NULL, NULL, '2025-07-07 16:52:42');
INSERT INTO `service_logs` (`id`, `service_id`, `status`, `response_time`, `error_message`, `additional_data`, `checked_at`) VALUES
(1497, 3, 1, 0.007593870162963867, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5804, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:42'),
(1498, 4, 1, 0.0035970211029052734, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8001, \"connections\": 2}', '2025-07-07 16:52:42'),
(1499, 5, 0, 0.003902, NULL, NULL, '2025-07-07 16:52:42'),
(1500, 6, 1, 0.003314, NULL, NULL, '2025-07-07 16:52:42'),
(1501, 7, 0, 0.00805211067199707, '', NULL, '2025-07-07 16:52:42'),
(1502, 1, 1, 0.012506, NULL, NULL, '2025-07-07 16:52:52'),
(1503, 2, 1, 0.0006411075592041016, NULL, NULL, '2025-07-07 16:52:52'),
(1504, 3, 1, 0.008114099502563477, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5814, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:52:52'),
(1505, 4, 1, 0.003302335739135742, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8011, \"connections\": 2}', '2025-07-07 16:52:52'),
(1506, 5, 0, 0.004105, NULL, NULL, '2025-07-07 16:52:52'),
(1507, 6, 1, 0.004234, NULL, NULL, '2025-07-07 16:52:52'),
(1508, 7, 0, 0.005448818206787109, '', NULL, '2025-07-07 16:52:52'),
(1509, 1, 1, 0.018456, NULL, NULL, '2025-07-07 16:53:02'),
(1510, 2, 1, 0.0005130767822265625, NULL, NULL, '2025-07-07 16:53:02'),
(1511, 3, 1, 0.005447864532470703, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5824, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:53:02'),
(1512, 4, 1, 0.007324934005737305, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8021, \"connections\": 2}', '2025-07-07 16:53:02'),
(1513, 5, 0, 0.005571, NULL, NULL, '2025-07-07 16:53:02'),
(1514, 6, 1, 0.00413, NULL, NULL, '2025-07-07 16:53:02'),
(1515, 7, 0, 0.01357722282409668, '', NULL, '2025-07-07 16:53:02'),
(1516, 1, 1, 0.012405, NULL, NULL, '2025-07-07 16:53:12'),
(1517, 2, 1, 0.0006909370422363281, NULL, NULL, '2025-07-07 16:53:12'),
(1518, 3, 1, 0.007869958877563477, NULL, '{\"version\": \"7.4.2\", \"uptime\": 5834, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:53:12'),
(1519, 4, 1, 0.003683805465698242, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8031, \"connections\": 2}', '2025-07-07 16:53:12'),
(1520, 5, 0, 0.003657, NULL, NULL, '2025-07-07 16:53:12'),
(1521, 6, 1, 0.003598, NULL, NULL, '2025-07-07 16:53:12'),
(1522, 7, 0, 0.008093118667602539, '', NULL, '2025-07-07 16:53:12'),
(1523, 1, 1, 0.029013, NULL, NULL, '2025-07-07 16:56:11'),
(1524, 2, 1, 0.0006611347198486328, NULL, NULL, '2025-07-07 16:56:11'),
(1525, 3, 1, 0.009898900985717773, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6013, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:56:11'),
(1526, 4, 1, 0.009851932525634766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8210, \"connections\": 2}', '2025-07-07 16:56:11'),
(1527, 5, 0, 0.008638, NULL, NULL, '2025-07-07 16:56:11'),
(1528, 6, 1, 0.007252, NULL, NULL, '2025-07-07 16:56:11'),
(1529, 7, 0, 0.025178909301757812, '', NULL, '2025-07-07 16:56:11'),
(1530, 1, 1, 0.021809, NULL, NULL, '2025-07-07 16:56:16'),
(1531, 2, 1, 0.004934072494506836, NULL, NULL, '2025-07-07 16:56:16'),
(1532, 3, 1, 0.014224052429199219, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6018, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:56:16'),
(1533, 4, 1, 0.005702972412109375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8215, \"connections\": 2}', '2025-07-07 16:56:16'),
(1534, 5, 0, 0.011454, NULL, NULL, '2025-07-07 16:56:16'),
(1535, 6, 1, 0.004033, NULL, NULL, '2025-07-07 16:56:16'),
(1536, 7, 0, 0.009849071502685547, '', NULL, '2025-07-07 16:56:16'),
(1537, 1, 1, 0.011233, NULL, NULL, '2025-07-07 16:56:21'),
(1538, 2, 1, 0.0008599758148193359, NULL, NULL, '2025-07-07 16:56:21'),
(1539, 3, 1, 0.0051229000091552734, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6023, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 16:56:21'),
(1540, 4, 1, 0.005930900573730469, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8220, \"connections\": 2}', '2025-07-07 16:56:21'),
(1541, 5, 0, 0.004954, NULL, NULL, '2025-07-07 16:56:21'),
(1542, 6, 1, 0.003676, NULL, NULL, '2025-07-07 16:56:21'),
(1543, 7, 0, 0.008042097091674805, '', NULL, '2025-07-07 16:56:21'),
(1544, 1, 1, 0.014855, NULL, NULL, '2025-07-07 17:02:21'),
(1545, 2, 1, 0.0005500316619873047, NULL, NULL, '2025-07-07 17:02:21'),
(1546, 3, 1, 0.010404109954833984, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6383, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:02:21'),
(1547, 4, 1, 0.007042884826660156, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8580, \"connections\": 6}', '2025-07-07 17:02:21'),
(1548, 5, 0, 0.00519, NULL, NULL, '2025-07-07 17:02:21'),
(1549, 6, 1, 0.0091, NULL, NULL, '2025-07-07 17:02:21'),
(1550, 7, 0, 0.027459144592285156, '', NULL, '2025-07-07 17:02:21'),
(1551, 1, 1, 0.014527, NULL, NULL, '2025-07-07 17:02:31'),
(1552, 2, 1, 0.0008339881896972656, NULL, NULL, '2025-07-07 17:02:31'),
(1553, 3, 1, 0.005686044692993164, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6393, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:02:31'),
(1554, 4, 1, 0.008419036865234375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8590, \"connections\": 6}', '2025-07-07 17:02:31'),
(1555, 5, 0, 0.004449, NULL, NULL, '2025-07-07 17:02:31'),
(1556, 6, 1, 0.00525, NULL, NULL, '2025-07-07 17:02:31'),
(1557, 7, 0, 0.01917099952697754, '', NULL, '2025-07-07 17:02:31'),
(1558, 1, 1, 0.015666, NULL, NULL, '2025-07-07 17:02:41'),
(1559, 2, 1, 0.0008790493011474609, NULL, NULL, '2025-07-07 17:02:41'),
(1560, 3, 1, 0.007157087326049805, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6403, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:02:41'),
(1561, 4, 1, 0.0034270286560058594, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8600, \"connections\": 6}', '2025-07-07 17:02:41'),
(1562, 5, 0, 0.003397, NULL, NULL, '2025-07-07 17:02:41'),
(1563, 6, 1, 0.004947, NULL, NULL, '2025-07-07 17:02:41'),
(1564, 7, 0, 0.008089780807495117, '', NULL, '2025-07-07 17:02:41'),
(1565, 1, 1, 0.01405, NULL, NULL, '2025-07-07 17:02:51'),
(1566, 2, 1, 0.0011382102966308594, NULL, NULL, '2025-07-07 17:02:51'),
(1567, 3, 1, 0.00817108154296875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6413, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:02:51'),
(1568, 4, 1, 0.0033919811248779297, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8610, \"connections\": 6}', '2025-07-07 17:02:51'),
(1569, 5, 0, 0.003269, NULL, NULL, '2025-07-07 17:02:51'),
(1570, 6, 1, 0.004768, NULL, NULL, '2025-07-07 17:02:51'),
(1571, 7, 0, 0.008976221084594727, '', NULL, '2025-07-07 17:02:51'),
(1572, 1, 1, 0.011915, NULL, NULL, '2025-07-07 17:04:57'),
(1573, 2, 1, 0.0005440711975097656, NULL, NULL, '2025-07-07 17:04:57'),
(1574, 3, 1, 0.007934331893920898, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6539, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:04:57'),
(1575, 4, 1, 0.0030701160430908203, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8736, \"connections\": 6}', '2025-07-07 17:04:57'),
(1576, 5, 0, 0.004946, NULL, NULL, '2025-07-07 17:04:57'),
(1577, 6, 1, 0.004227, NULL, NULL, '2025-07-07 17:04:57'),
(1578, 7, 0, 0.025225162506103516, '', NULL, '2025-07-07 17:04:57'),
(1579, 1, 1, 0.023031, NULL, NULL, '2025-07-07 17:05:02'),
(1580, 2, 1, 0.001100778579711914, NULL, NULL, '2025-07-07 17:05:02'),
(1581, 3, 1, 0.007905960083007812, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6544, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:02'),
(1582, 4, 1, 0.0044672489166259766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8741, \"connections\": 6}', '2025-07-07 17:05:02'),
(1583, 5, 0, 0.004301, NULL, NULL, '2025-07-07 17:05:02'),
(1584, 6, 1, 0.003619, NULL, NULL, '2025-07-07 17:05:02'),
(1585, 7, 0, 0.008748054504394531, '', NULL, '2025-07-07 17:05:02'),
(1586, 1, 1, 0.014917, NULL, NULL, '2025-07-07 17:05:07'),
(1587, 2, 1, 0.0006830692291259766, NULL, NULL, '2025-07-07 17:05:07'),
(1588, 3, 1, 0.010787248611450195, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6549, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:07'),
(1589, 4, 1, 0.008610248565673828, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8746, \"connections\": 6}', '2025-07-07 17:05:07'),
(1590, 5, 0, 0.005746, NULL, NULL, '2025-07-07 17:05:07'),
(1591, 6, 1, 0.003968, NULL, NULL, '2025-07-07 17:05:07'),
(1592, 7, 0, 0.04475712776184082, '', NULL, '2025-07-07 17:05:08'),
(1593, 1, 1, 0.010135, NULL, NULL, '2025-07-07 17:05:12'),
(1594, 2, 1, 0.0006930828094482422, NULL, NULL, '2025-07-07 17:05:12'),
(1595, 3, 1, 0.006794929504394531, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6554, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:12'),
(1596, 4, 1, 0.004745960235595703, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8751, \"connections\": 6}', '2025-07-07 17:05:12'),
(1597, 5, 0, 0.003658, NULL, NULL, '2025-07-07 17:05:12'),
(1598, 6, 1, 0.004864, NULL, NULL, '2025-07-07 17:05:12'),
(1599, 7, 0, 0.007539987564086914, '', NULL, '2025-07-07 17:05:12'),
(1600, 1, 1, 0.025802, NULL, NULL, '2025-07-07 17:05:17'),
(1601, 2, 1, 0.00448298454284668, NULL, NULL, '2025-07-07 17:05:17'),
(1602, 3, 1, 0.0166928768157959, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6559, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:17'),
(1603, 4, 1, 0.004414081573486328, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8756, \"connections\": 6}', '2025-07-07 17:05:17'),
(1604, 5, 0, 0.005886, NULL, NULL, '2025-07-07 17:05:17'),
(1605, 6, 1, 0.004812, NULL, NULL, '2025-07-07 17:05:17'),
(1606, 7, 0, 0.014457941055297852, '', NULL, '2025-07-07 17:05:17'),
(1607, 1, 1, 0.011639, NULL, NULL, '2025-07-07 17:05:22'),
(1608, 2, 1, 0.0008928775787353516, NULL, NULL, '2025-07-07 17:05:22'),
(1609, 3, 1, 0.013231754302978516, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6564, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:22'),
(1610, 4, 1, 0.007035970687866211, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8761, \"connections\": 6}', '2025-07-07 17:05:22'),
(1611, 5, 0, 0.009388, NULL, NULL, '2025-07-07 17:05:22'),
(1612, 6, 1, 0.008526, NULL, NULL, '2025-07-07 17:05:22'),
(1613, 7, 0, 0.015282154083251953, '', NULL, '2025-07-07 17:05:22'),
(1614, 1, 1, 0.015334, NULL, NULL, '2025-07-07 17:05:28'),
(1615, 2, 1, 0.0012137889862060547, NULL, NULL, '2025-07-07 17:05:28'),
(1616, 3, 1, 0.008147239685058594, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6570, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:28'),
(1617, 4, 1, 0.008791923522949219, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8767, \"connections\": 6}', '2025-07-07 17:05:28'),
(1618, 5, 0, 0.012359, NULL, NULL, '2025-07-07 17:05:28'),
(1619, 6, 1, 0.009842, NULL, NULL, '2025-07-07 17:05:28'),
(1620, 7, 0, 0.02536296844482422, '', NULL, '2025-07-07 17:05:28'),
(1621, 1, 1, 0.021549, NULL, NULL, '2025-07-07 17:05:32'),
(1622, 2, 1, 0.0007920265197753906, NULL, NULL, '2025-07-07 17:05:32'),
(1623, 3, 1, 0.008916139602661133, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6574, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:32'),
(1624, 4, 1, 0.005834102630615234, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8771, \"connections\": 6}', '2025-07-07 17:05:32'),
(1625, 5, 0, 0.050269, NULL, NULL, '2025-07-07 17:05:32'),
(1626, 6, 1, 0.007559, NULL, NULL, '2025-07-07 17:05:32'),
(1627, 7, 0, 0.008940935134887695, '', NULL, '2025-07-07 17:05:32'),
(1628, 1, 1, 0.07953, NULL, NULL, '2025-07-07 17:05:58'),
(1629, 2, 1, 0.001657247543334961, NULL, NULL, '2025-07-07 17:05:58'),
(1630, 3, 1, 0.009101152420043945, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6600, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:05:58'),
(1631, 4, 1, 0.005864143371582031, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8797, \"connections\": 6}', '2025-07-07 17:05:58'),
(1632, 5, 0, 0.027759, NULL, NULL, '2025-07-07 17:05:58'),
(1633, 6, 1, 0.00655, NULL, NULL, '2025-07-07 17:05:58'),
(1634, 7, 0, 0.02006816864013672, '', NULL, '2025-07-07 17:05:58'),
(1635, 1, 1, 0.011544, NULL, NULL, '2025-07-07 17:06:08'),
(1636, 2, 1, 0.00043392181396484375, NULL, NULL, '2025-07-07 17:06:08'),
(1637, 3, 1, 0.00931406021118164, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6610, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:08'),
(1638, 4, 1, 0.004341840744018555, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8807, \"connections\": 6}', '2025-07-07 17:06:08'),
(1639, 5, 0, 0.004595, NULL, NULL, '2025-07-07 17:06:08'),
(1640, 6, 1, 0.005748, NULL, NULL, '2025-07-07 17:06:08'),
(1641, 7, 0, 0.010839223861694336, '', NULL, '2025-07-07 17:06:08'),
(1642, 1, 1, 0.016335, NULL, NULL, '2025-07-07 17:06:18'),
(1643, 2, 1, 0.0008339881896972656, NULL, NULL, '2025-07-07 17:06:18'),
(1644, 3, 1, 0.04323005676269531, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6620, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:18'),
(1645, 4, 1, 0.005825996398925781, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8817, \"connections\": 6}', '2025-07-07 17:06:18'),
(1646, 5, 0, 0.003832, NULL, NULL, '2025-07-07 17:06:18'),
(1647, 6, 1, 0.004421, NULL, NULL, '2025-07-07 17:06:18'),
(1648, 7, 0, 0.015916109085083008, '', NULL, '2025-07-07 17:06:18'),
(1649, 1, 1, 0.022084, NULL, NULL, '2025-07-07 17:06:28'),
(1650, 2, 1, 0.0015499591827392578, NULL, NULL, '2025-07-07 17:06:28'),
(1651, 3, 1, 0.005527019500732422, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6630, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:28'),
(1652, 4, 1, 0.0030317306518554688, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8827, \"connections\": 6}', '2025-07-07 17:06:28'),
(1653, 5, 0, 0.00991, NULL, NULL, '2025-07-07 17:06:28'),
(1654, 6, 1, 0.003604, NULL, NULL, '2025-07-07 17:06:28'),
(1655, 7, 0, 0.008978843688964844, '', NULL, '2025-07-07 17:06:28'),
(1656, 1, 1, 0.014869, NULL, NULL, '2025-07-07 17:06:38'),
(1657, 2, 1, 0.00047588348388671875, NULL, NULL, '2025-07-07 17:06:38'),
(1658, 3, 1, 0.011444807052612305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6640, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:38'),
(1659, 4, 1, 0.004204988479614258, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8837, \"connections\": 6}', '2025-07-07 17:06:38'),
(1660, 5, 0, 0.007194, NULL, NULL, '2025-07-07 17:06:38'),
(1661, 6, 1, 0.012649, NULL, NULL, '2025-07-07 17:06:38'),
(1662, 7, 0, 0.008635997772216797, '', NULL, '2025-07-07 17:06:38'),
(1663, 1, 1, 0.014917, NULL, NULL, '2025-07-07 17:06:48'),
(1664, 2, 1, 0.0006880760192871094, NULL, NULL, '2025-07-07 17:06:48'),
(1665, 3, 1, 0.010926008224487305, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6650, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:48'),
(1666, 4, 1, 0.0045697689056396484, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8847, \"connections\": 6}', '2025-07-07 17:06:48'),
(1667, 5, 0, 0.008797, NULL, NULL, '2025-07-07 17:06:48'),
(1668, 6, 1, 0.004358, NULL, NULL, '2025-07-07 17:06:48'),
(1669, 7, 0, 0.008411884307861328, '', NULL, '2025-07-07 17:06:48'),
(1670, 1, 1, 0.014972, NULL, NULL, '2025-07-07 17:06:58'),
(1671, 2, 1, 0.0005712509155273438, NULL, NULL, '2025-07-07 17:06:58'),
(1672, 3, 1, 0.009140968322753906, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6660, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:06:58'),
(1673, 4, 1, 0.0047321319580078125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8857, \"connections\": 6}', '2025-07-07 17:06:58'),
(1674, 5, 0, 0.004886, NULL, NULL, '2025-07-07 17:06:58'),
(1675, 6, 1, 0.0051, NULL, NULL, '2025-07-07 17:06:58'),
(1676, 7, 0, 0.012630939483642578, '', NULL, '2025-07-07 17:06:58'),
(1677, 1, 1, 0.018237, NULL, NULL, '2025-07-07 17:07:08'),
(1678, 2, 1, 0.0007638931274414062, NULL, NULL, '2025-07-07 17:07:08'),
(1679, 3, 1, 0.011822700500488281, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6670, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:07:08'),
(1680, 4, 1, 0.003676176071166992, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8867, \"connections\": 6}', '2025-07-07 17:07:08'),
(1681, 5, 0, 0.010019, NULL, NULL, '2025-07-07 17:07:08'),
(1682, 6, 1, 0.008961, NULL, NULL, '2025-07-07 17:07:08'),
(1683, 7, 0, 0.00988912582397461, '', NULL, '2025-07-07 17:07:08'),
(1684, 1, 1, 0.015772, NULL, NULL, '2025-07-07 17:07:18'),
(1685, 2, 1, 0.006675004959106445, NULL, NULL, '2025-07-07 17:07:18'),
(1686, 3, 1, 0.036847829818725586, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6680, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:07:18'),
(1687, 4, 1, 0.005983829498291016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8877, \"connections\": 6}', '2025-07-07 17:07:18'),
(1688, 5, 0, 0.006503, NULL, NULL, '2025-07-07 17:07:18'),
(1689, 6, 1, 0.005696, NULL, NULL, '2025-07-07 17:07:18'),
(1690, 7, 0, 0.012559652328491211, '', NULL, '2025-07-07 17:07:18'),
(1691, 1, 1, 0.009038, NULL, NULL, '2025-07-07 17:07:28'),
(1692, 2, 1, 0.0006060600280761719, NULL, NULL, '2025-07-07 17:07:28'),
(1693, 3, 1, 0.006433010101318359, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6690, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:07:28'),
(1694, 4, 1, 0.0033960342407226562, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8887, \"connections\": 6}', '2025-07-07 17:07:28'),
(1695, 5, 0, 0.00413, NULL, NULL, '2025-07-07 17:07:28'),
(1696, 6, 1, 0.004215, NULL, NULL, '2025-07-07 17:07:28'),
(1697, 7, 0, 0.0095977783203125, '', NULL, '2025-07-07 17:07:28'),
(1698, 1, 1, 0.024496, NULL, NULL, '2025-07-07 17:07:38'),
(1699, 2, 1, 0.00046634674072265625, NULL, NULL, '2025-07-07 17:07:38'),
(1700, 3, 1, 0.10559201240539551, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6700, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:07:38'),
(1701, 4, 1, 0.0041179656982421875, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8897, \"connections\": 6}', '2025-07-07 17:07:38'),
(1702, 5, 0, 0.003686, NULL, NULL, '2025-07-07 17:07:38'),
(1703, 6, 1, 0.003994, NULL, NULL, '2025-07-07 17:07:38'),
(1704, 7, 0, 0.07885479927062988, '', NULL, '2025-07-07 17:07:38'),
(1705, 1, 1, 0.014085, NULL, NULL, '2025-07-07 17:08:21'),
(1706, 2, 1, 0.0009839534759521484, NULL, NULL, '2025-07-07 17:08:21'),
(1707, 3, 1, 0.007012844085693359, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6743, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:08:21'),
(1708, 4, 1, 0.007664918899536133, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8940, \"connections\": 6}', '2025-07-07 17:08:21'),
(1709, 5, 0, 0.004347, NULL, NULL, '2025-07-07 17:08:22'),
(1710, 6, 1, 0.00411, NULL, NULL, '2025-07-07 17:08:22'),
(1711, 7, 0, 0.22240710258483887, '', NULL, '2025-07-07 17:08:22'),
(1712, 1, 1, 0.015004, NULL, NULL, '2025-07-07 17:08:57'),
(1713, 2, 1, 0.0008609294891357422, NULL, NULL, '2025-07-07 17:08:57'),
(1714, 3, 1, 0.0100250244140625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6779, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:08:57'),
(1715, 4, 1, 0.008508920669555664, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8976, \"connections\": 6}', '2025-07-07 17:08:57'),
(1716, 5, 0, 0.003946, NULL, NULL, '2025-07-07 17:08:57'),
(1717, 6, 1, 0.007579, NULL, NULL, '2025-07-07 17:08:57'),
(1718, 7, 0, 0.013998031616210938, '', NULL, '2025-07-07 17:08:57'),
(1719, 1, 1, 0.020794, NULL, NULL, '2025-07-07 17:09:07'),
(1720, 2, 1, 0.001154184341430664, NULL, NULL, '2025-07-07 17:09:07'),
(1721, 3, 1, 0.007256984710693359, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6789, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:09:07'),
(1722, 4, 1, 0.00785684585571289, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8986, \"connections\": 6}', '2025-07-07 17:09:07'),
(1723, 5, 0, 0.005429, NULL, NULL, '2025-07-07 17:09:07'),
(1724, 6, 1, 0.007761, NULL, NULL, '2025-07-07 17:09:07'),
(1725, 7, 0, 0.06288695335388184, '', NULL, '2025-07-07 17:09:07'),
(1726, 1, 1, 0.013386, NULL, NULL, '2025-07-07 17:09:17'),
(1727, 2, 1, 0.0006089210510253906, NULL, NULL, '2025-07-07 17:09:17'),
(1728, 3, 1, 0.008217096328735352, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6799, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:09:17'),
(1729, 4, 1, 0.004065990447998047, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 8996, \"connections\": 6}', '2025-07-07 17:09:17'),
(1730, 5, 0, 0.009182, NULL, NULL, '2025-07-07 17:09:17'),
(1731, 6, 1, 0.016477, NULL, NULL, '2025-07-07 17:09:17'),
(1732, 7, 0, 0.007502079010009766, '', NULL, '2025-07-07 17:09:17'),
(1733, 1, 1, 0.018777, NULL, NULL, '2025-07-07 17:09:27'),
(1734, 2, 1, 0.002620220184326172, NULL, NULL, '2025-07-07 17:09:27'),
(1735, 3, 1, 0.02257513999938965, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6809, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:09:27'),
(1736, 4, 1, 0.00861501693725586, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 9006, \"connections\": 6}', '2025-07-07 17:09:27'),
(1737, 5, 0, 0.005283, NULL, NULL, '2025-07-07 17:09:27'),
(1738, 6, 1, 0.005391, NULL, NULL, '2025-07-07 17:09:27'),
(1739, 7, 0, 0.016466140747070312, '', NULL, '2025-07-07 17:09:27'),
(1740, 1, 1, 0.00908, NULL, NULL, '2025-07-07 17:09:37'),
(1741, 2, 1, 0.0009636878967285156, NULL, NULL, '2025-07-07 17:09:37'),
(1742, 3, 1, 0.009567975997924805, NULL, '{\"version\": \"7.4.2\", \"uptime\": 6819, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 17:09:37'),
(1743, 4, 1, 0.004923105239868164, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 9016, \"connections\": 6}', '2025-07-07 17:09:37'),
(1744, 5, 0, 0.004336, NULL, NULL, '2025-07-07 17:09:37'),
(1745, 6, 1, 0.004671, NULL, NULL, '2025-07-07 17:09:37'),
(1746, 7, 0, 0.01742696762084961, '', NULL, '2025-07-07 17:09:37'),
(1747, 1, 1, 0.020131, NULL, NULL, '2025-07-07 18:30:02'),
(1748, 2, 1, 0.0010061264038085938, NULL, NULL, '2025-07-07 18:30:02'),
(1749, 3, 1, 0.0288541316986084, NULL, '{\"version\": \"7.4.2\", \"uptime\": 11644, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:30:02'),
(1750, 4, 1, 0.030621051788330078, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 13841, \"connections\": 6}', '2025-07-07 18:30:02'),
(1751, 5, 0, 0.01514, NULL, NULL, '2025-07-07 18:30:02'),
(1752, 6, 1, 0.005631, NULL, NULL, '2025-07-07 18:30:02'),
(1753, 7, 0, 0.025114774703979492, '', NULL, '2025-07-07 18:30:02'),
(1754, 1, 1, 0.015111, NULL, NULL, '2025-07-07 18:30:11'),
(1755, 2, 1, 0.0005500316619873047, NULL, NULL, '2025-07-07 18:30:11'),
(1756, 3, 1, 0.00851583480834961, NULL, '{\"version\": \"7.4.2\", \"uptime\": 11653, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:30:11'),
(1757, 4, 1, 0.00362396240234375, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 13850, \"connections\": 6}', '2025-07-07 18:30:11'),
(1758, 5, 0, 0.003768, NULL, NULL, '2025-07-07 18:30:11'),
(1759, 6, 1, 0.007315, NULL, NULL, '2025-07-07 18:30:11'),
(1760, 7, 0, 0.013769865036010742, '', NULL, '2025-07-07 18:30:12'),
(1761, 1, 1, 0.01246, NULL, NULL, '2025-07-07 18:30:21'),
(1762, 2, 1, 0.0008559226989746094, NULL, NULL, '2025-07-07 18:30:21'),
(1763, 3, 1, 0.00550079345703125, NULL, '{\"version\": \"7.4.2\", \"uptime\": 11663, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:30:21'),
(1764, 4, 1, 0.002995014190673828, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 13860, \"connections\": 6}', '2025-07-07 18:30:21'),
(1765, 5, 0, 0.007032, NULL, NULL, '2025-07-07 18:30:21'),
(1766, 6, 1, 0.004933, NULL, NULL, '2025-07-07 18:30:21'),
(1767, 7, 0, 0.014854192733764648, '', NULL, '2025-07-07 18:30:22'),
(1768, 1, 1, 0.014794, NULL, NULL, '2025-07-07 18:34:50'),
(1769, 2, 1, 0.0007002353668212891, NULL, NULL, '2025-07-07 18:34:50'),
(1770, 3, 1, 0.010598897933959961, NULL, '{\"version\": \"7.4.2\", \"uptime\": 11932, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:34:50'),
(1771, 4, 1, 0.0052378177642822266, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 14129, \"connections\": 6}', '2025-07-07 18:34:50'),
(1772, 5, 0, 0.00506, NULL, NULL, '2025-07-07 18:34:51'),
(1773, 6, 1, 0.007618, NULL, NULL, '2025-07-07 18:34:51'),
(1774, 7, 0, 0.016785144805908203, '', NULL, '2025-07-07 18:34:51'),
(1775, 1, 1, 0.011818, NULL, NULL, '2025-07-07 18:34:55'),
(1776, 2, 1, 0.0019080638885498047, NULL, NULL, '2025-07-07 18:34:55'),
(1777, 3, 1, 0.007946014404296875, NULL, '{\"version\": \"7.4.2\", \"uptime\": 11937, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:34:55'),
(1778, 4, 1, 0.007030963897705078, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 14134, \"connections\": 6}', '2025-07-07 18:34:55'),
(1779, 5, 0, 0.016206, NULL, NULL, '2025-07-07 18:34:55'),
(1780, 6, 1, 0.004969, NULL, NULL, '2025-07-07 18:34:55'),
(1781, 7, 0, 0.015290021896362305, '', NULL, '2025-07-07 18:34:55'),
(1782, 1, 1, 0.013968, NULL, NULL, '2025-07-07 18:37:11'),
(1783, 2, 1, 0.0007028579711914062, NULL, NULL, '2025-07-07 18:37:11'),
(1784, 3, 1, 0.020175933837890625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 12073, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 18:37:11'),
(1785, 4, 1, 0.009280681610107422, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 14270, \"connections\": 6}', '2025-07-07 18:37:11'),
(1786, 5, 0, 0.016177, NULL, NULL, '2025-07-07 18:37:11'),
(1787, 6, 1, 0.010122, NULL, NULL, '2025-07-07 18:37:11'),
(1788, 7, 0, 0.10471010208129883, '', NULL, '2025-07-07 18:37:11'),
(1789, 1, 1, 0.022188, NULL, NULL, '2025-07-07 19:27:35'),
(1790, 2, 1, 0.0008580684661865234, NULL, NULL, '2025-07-07 19:27:35'),
(1791, 3, 1, 0.014178037643432617, NULL, '{\"version\": \"7.4.2\", \"uptime\": 15097, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 19:27:35'),
(1792, 4, 1, 0.011089086532592773, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 17294, \"connections\": 4}', '2025-07-07 19:27:35'),
(1793, 5, 0, 0.011552, NULL, NULL, '2025-07-07 19:27:35'),
(1794, 6, 1, 0.011105, NULL, NULL, '2025-07-07 19:27:35'),
(1795, 7, 0, 0.07141804695129395, '', NULL, '2025-07-07 19:27:35'),
(1796, 1, 1, 0.029923, NULL, NULL, '2025-07-07 20:09:16'),
(1797, 2, 1, 0.0007719993591308594, NULL, NULL, '2025-07-07 20:09:16'),
(1798, 3, 1, 0.008566141128540039, NULL, '{\"version\": \"7.4.2\", \"uptime\": 17599, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-07 20:09:17'),
(1799, 4, 1, 0.013760089874267578, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 19796, \"connections\": 4}', '2025-07-07 20:09:17'),
(1800, 5, 0, 0.008956, NULL, NULL, '2025-07-07 20:09:17'),
(1801, 6, 1, 0.014801, NULL, NULL, '2025-07-07 20:09:17'),
(1802, 7, 0, 0.030138015747070312, '', NULL, '2025-07-07 20:09:17'),
(1803, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110af3290>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:13'),
(1804, 2, 0, 0.0005061626434326172, NULL, NULL, '2025-07-08 01:15:13'),
(1805, 3, 0, 0.004370212554931641, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:15:13'),
(1806, 4, 1, 0.007829904556274414, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 465, \"connections\": 6}', '2025-07-08 01:15:13'),
(1807, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bc9110>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:13'),
(1808, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110be63d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:13'),
(1809, 7, 0, 0.07802915573120117, '', NULL, '2025-07-08 01:15:13'),
(1810, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110869550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:23'),
(1811, 2, 0, 0.00038695335388183594, NULL, NULL, '2025-07-08 01:15:23'),
(1812, 3, 0, 0.0014178752899169922, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:15:23'),
(1813, 4, 1, 0.01620316505432129, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 475, \"connections\": 6}', '2025-07-08 01:15:23'),
(1814, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bdf550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:23'),
(1815, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c29890>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:23'),
(1816, 7, 0, 0.0763707160949707, '', NULL, '2025-07-08 01:15:23'),
(1817, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2e7d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:33'),
(1818, 2, 0, 0.010075807571411133, NULL, NULL, '2025-07-08 01:15:33'),
(1819, 3, 0, 0.0028281211853027344, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:15:33'),
(1820, 4, 1, 0.020010948181152344, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 485, \"connections\": 6}', '2025-07-08 01:15:33'),
(1821, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2a6d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:33'),
(1822, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110be4d90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:33'),
(1823, 7, 0, 0.0365300178527832, '', NULL, '2025-07-08 01:15:33'),
(1824, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2fb90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:43'),
(1825, 2, 0, 0.0026459693908691406, NULL, NULL, '2025-07-08 01:15:43'),
(1826, 3, 0, 0.0012748241424560547, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:15:43'),
(1827, 4, 1, 0.0049228668212890625, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 495, \"connections\": 6}', '2025-07-08 01:15:43'),
(1828, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bdd990>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:43'),
(1829, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bdfbd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:43'),
(1830, 7, 0, 0.11117887496948242, '', NULL, '2025-07-08 01:15:43'),
(1831, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c39450>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:53'),
(1832, 2, 0, 0.0006139278411865234, NULL, NULL, '2025-07-08 01:15:53'),
(1833, 3, 0, 0.008533000946044922, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:15:53'),
(1834, 4, 1, 0.018857955932617188, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 505, \"connections\": 6}', '2025-07-08 01:15:53'),
(1835, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2f050>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:53'),
(1836, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bddcd0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:15:53'),
(1837, 7, 0, 0.16368484497070312, '', NULL, '2025-07-08 01:15:53'),
(1838, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2a850>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:03'),
(1839, 2, 0, 0.004140138626098633, NULL, NULL, '2025-07-08 01:16:03'),
(1840, 3, 0, 0.0024099349975585938, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:03'),
(1841, 4, 1, 0.022989988327026367, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 515, \"connections\": 6}', '2025-07-08 01:16:03'),
(1842, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110be7f90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:03'),
(1843, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2a850>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:03'),
(1844, 7, 0, 0.10424494743347168, '', NULL, '2025-07-08 01:16:03'),
(1845, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c40090>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:13'),
(1846, 2, 0, 0.0031616687774658203, NULL, NULL, '2025-07-08 01:16:13'),
(1847, 3, 0, 0.007823705673217773, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:13'),
(1848, 4, 1, 0.030131101608276367, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 525, \"connections\": 6}', '2025-07-08 01:16:13'),
(1849, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c40a50>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:13'),
(1850, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c48ed0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:13'),
(1851, 7, 0, 0.06371617317199707, '', NULL, '2025-07-08 01:16:13'),
(1852, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c41250>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:23'),
(1853, 2, 0, 0.0010960102081298828, NULL, NULL, '2025-07-08 01:16:23'),
(1854, 3, 0, 0.0016851425170898438, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:23'),
(1855, 4, 1, 0.010732889175415039, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 535, \"connections\": 6}', '2025-07-08 01:16:23'),
(1856, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bca1d0>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:23'),
(1857, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bded90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:23'),
(1858, 7, 0, 0.04979896545410156, '', NULL, '2025-07-08 01:16:23'),
(1859, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c29d10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:33'),
(1860, 2, 0, 0.0007319450378417969, NULL, NULL, '2025-07-08 01:16:33'),
(1861, 3, 0, 0.004986763000488281, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:33'),
(1862, 4, 1, 0.10611701011657715, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 545, \"connections\": 6}', '2025-07-08 01:16:33'),
(1863, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c3a250>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:33'),
(1864, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2a090>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:33'),
(1865, 7, 0, 0.043892860412597656, '', NULL, '2025-07-08 01:16:33'),
(1866, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c43990>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:43'),
(1867, 2, 0, 0.00045013427734375, NULL, NULL, '2025-07-08 01:16:43'),
(1868, 3, 0, 0.0022389888763427734, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:43'),
(1869, 4, 1, 0.01016688346862793, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 555, \"connections\": 6}', '2025-07-08 01:16:43'),
(1870, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c4ae10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:43'),
(1871, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110bdce10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:43'),
(1872, 7, 0, 0.021786212921142578, '', NULL, '2025-07-08 01:16:43'),
(1873, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c3b750>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:53'),
(1874, 2, 0, 0.0007312297821044922, NULL, NULL, '2025-07-08 01:16:53'),
(1875, 3, 0, 0.0057621002197265625, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:16:53'),
(1876, 4, 1, 0.012048959732055664, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 565, \"connections\": 6}', '2025-07-08 01:16:53'),
(1877, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c43f90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:53'),
(1878, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c4bb90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:16:53'),
(1879, 7, 0, 0.1846621036529541, '', NULL, '2025-07-08 01:16:53'),
(1880, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2d550>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:03'),
(1881, 2, 0, 0.004599094390869141, NULL, NULL, '2025-07-08 01:17:03'),
(1882, 3, 0, 0.001522064208984375, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:17:03'),
(1883, 4, 1, 0.01584315299987793, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 575, \"connections\": 6}', '2025-07-08 01:17:03'),
(1884, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c29a10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:03'),
(1885, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2b310>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:03'),
(1886, 7, 0, 0.033143043518066406, '', NULL, '2025-07-08 01:17:03'),
(1887, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c48090>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:13'),
(1888, 2, 0, 0.003584146499633789, NULL, NULL, '2025-07-08 01:17:13'),
(1889, 3, 0, 0.0071599483489990234, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:17:13'),
(1890, 4, 1, 0.010492801666259766, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 585, \"connections\": 6}', '2025-07-08 01:17:13'),
(1891, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2c710>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:13'),
(1892, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2b250>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:13'),
(1893, 7, 0, 0.01987290382385254, '', NULL, '2025-07-08 01:17:13'),
(1894, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c3b750>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:23'),
(1895, 2, 0, 0.0026051998138427734, NULL, NULL, '2025-07-08 01:17:23'),
(1896, 3, 0, 0.001753091812133789, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:17:23'),
(1897, 4, 1, 0.0060732364654541016, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 595, \"connections\": 6}', '2025-07-08 01:17:23'),
(1898, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2a590>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:23'),
(1899, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2ad90>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:23'),
(1900, 7, 0, 0.03199577331542969, '', NULL, '2025-07-08 01:17:23'),
(1901, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110be5090>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:33'),
(1902, 2, 0, 0.005392789840698242, NULL, NULL, '2025-07-08 01:17:33'),
(1903, 3, 0, 0.00904703140258789, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:17:33'),
(1904, 4, 1, 0.3801112174987793, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 605, \"connections\": 6}', '2025-07-08 01:17:33'),
(1905, 5, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=6333): Max retries exceeded with url: /health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c39c10>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:33'),
(1906, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c3b990>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:33'),
(1907, 7, 0, 0.04006195068359375, '', NULL, '2025-07-08 01:17:33'),
(1908, 1, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9200): Max retries exceeded with url: /_cluster/health (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c40050>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:43'),
(1909, 2, 1, 0.0013318061828613281, NULL, NULL, '2025-07-08 01:17:43'),
(1910, 3, 0, 0.0033309459686279297, 'Error 61 connecting to localhost:6379. Connection refused.', NULL, '2025-07-08 01:17:43'),
(1911, 4, 1, 0.00613093376159668, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 615, \"connections\": 6}', '2025-07-08 01:17:43'),
(1912, 5, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:17:43'),
(1913, 6, 0, NULL, 'HTTPConnectionPool(host=\'localhost\', port=9500): Max retries exceeded with url: /minio/health/live (Caused by NewConnectionError(\'<urllib3.connection.HTTPConnection object at 0x110c2e050>: Failed to establish a new connection: [Errno 61] Connection refused\'))', NULL, '2025-07-08 01:17:43'),
(1914, 7, 0, 0.08053803443908691, '', NULL, '2025-07-08 01:17:43'),
(1915, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:17:53'),
(1916, 2, 1, 0.0006647109985351562, NULL, NULL, '2025-07-08 01:17:53'),
(1917, 3, 1, 0.0504910945892334, NULL, '{\"version\": \"7.4.2\", \"uptime\": 7, \"used_memory\": \"1012.10K\", \"connected_clients\": 1}', '2025-07-08 01:17:53'),
(1918, 4, 1, 0.004840850830078125, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 625, \"connections\": 6}', '2025-07-08 01:17:53'),
(1919, 5, 0, 0.040924, NULL, NULL, '2025-07-08 01:17:53'),
(1920, 6, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:17:53'),
(1921, 7, 0, 0.02667689323425293, '', NULL, '2025-07-08 01:17:53'),
(1922, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:03'),
(1923, 2, 1, 0.0006768703460693359, NULL, NULL, '2025-07-08 01:18:03'),
(1924, 3, 1, 0.017852067947387695, NULL, '{\"version\": \"7.4.2\", \"uptime\": 17, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:18:03'),
(1925, 4, 1, 0.009253978729248047, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 635, \"connections\": 6}', '2025-07-08 01:18:03'),
(1926, 5, 0, 0.010315, NULL, NULL, '2025-07-08 01:18:03'),
(1927, 6, 1, 0.012881, NULL, NULL, '2025-07-08 01:18:03'),
(1928, 7, 0, 0.04663395881652832, '', NULL, '2025-07-08 01:18:03'),
(1929, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:13'),
(1930, 2, 1, 0.00046706199645996094, NULL, NULL, '2025-07-08 01:18:13'),
(1931, 3, 1, 0.02030205726623535, NULL, '{\"version\": \"7.4.2\", \"uptime\": 27, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:18:13'),
(1932, 4, 1, 0.009642601013183594, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 645, \"connections\": 6}', '2025-07-08 01:18:13'),
(1933, 5, 0, 0.00547, NULL, NULL, '2025-07-08 01:18:13'),
(1934, 6, 1, 0.058628, NULL, NULL, '2025-07-08 01:18:13');
INSERT INTO `service_logs` (`id`, `service_id`, `status`, `response_time`, `error_message`, `additional_data`, `checked_at`) VALUES
(1935, 7, 0, 0.03524208068847656, '', NULL, '2025-07-08 01:18:13'),
(1936, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:24'),
(1937, 2, 1, 0.0020143985748291016, NULL, NULL, '2025-07-08 01:18:24'),
(1938, 3, 1, 0.2305600643157959, NULL, '{\"version\": \"7.4.2\", \"uptime\": 38, \"used_memory\": \"1021.21K\", \"connected_clients\": 1}', '2025-07-08 01:18:24'),
(1939, 4, 1, 0.019292116165161133, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 656, \"connections\": 6}', '2025-07-08 01:18:24'),
(1940, 5, 0, 0.113781, NULL, NULL, '2025-07-08 01:18:24'),
(1941, 6, 1, 0.013925, NULL, NULL, '2025-07-08 01:18:24'),
(1942, 7, 0, 0.07252812385559082, '', NULL, '2025-07-08 01:18:24'),
(1943, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:33'),
(1944, 2, 1, 0.0006530284881591797, NULL, NULL, '2025-07-08 01:18:33'),
(1945, 3, 1, 0.07685303688049316, NULL, '{\"version\": \"7.4.2\", \"uptime\": 47, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:18:33'),
(1946, 4, 1, 0.006531238555908203, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 665, \"connections\": 6}', '2025-07-08 01:18:33'),
(1947, 5, 0, 0.099296, NULL, NULL, '2025-07-08 01:18:33'),
(1948, 6, 1, 0.014967, NULL, NULL, '2025-07-08 01:18:33'),
(1949, 7, 0, 0.05067276954650879, '', NULL, '2025-07-08 01:18:33'),
(1950, 2, 1, 0.0006010532379150391, NULL, NULL, '2025-07-08 01:18:37'),
(1951, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:43'),
(1952, 2, 1, 0.0011699199676513672, NULL, NULL, '2025-07-08 01:18:43'),
(1953, 3, 1, 0.014329910278320312, NULL, '{\"version\": \"7.4.2\", \"uptime\": 57, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:18:43'),
(1954, 4, 1, 0.006662130355834961, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 675, \"connections\": 6}', '2025-07-08 01:18:43'),
(1955, 5, 0, 0.012224, NULL, NULL, '2025-07-08 01:18:43'),
(1956, 6, 1, 0.074612, NULL, NULL, '2025-07-08 01:18:43'),
(1957, 7, 0, 0.13547801971435547, '', NULL, '2025-07-08 01:18:43'),
(1958, 6, 1, 0.036116, NULL, NULL, '2025-07-08 01:18:46'),
(1959, 4, 1, 0.006224870681762695, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 682, \"connections\": 6}', '2025-07-08 01:18:50'),
(1960, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:18:53'),
(1961, 2, 1, 0.0008330345153808594, NULL, NULL, '2025-07-08 01:18:53'),
(1962, 3, 1, 0.13821697235107422, NULL, '{\"version\": \"7.4.2\", \"uptime\": 67, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:18:53'),
(1963, 4, 1, 0.00762486457824707, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 685, \"connections\": 6}', '2025-07-08 01:18:53'),
(1964, 5, 0, 0.05231, NULL, NULL, '2025-07-08 01:18:53'),
(1965, 6, 1, 0.018822, NULL, NULL, '2025-07-08 01:18:53'),
(1966, 7, 0, 0.043882131576538086, '', NULL, '2025-07-08 01:18:53'),
(1967, 5, 0, 0.022566, NULL, NULL, '2025-07-08 01:19:02'),
(1968, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:03'),
(1969, 2, 1, 0.0036728382110595703, NULL, NULL, '2025-07-08 01:19:03'),
(1970, 3, 1, 0.28368687629699707, NULL, '{\"version\": \"7.4.2\", \"uptime\": 77, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:03'),
(1971, 4, 1, 0.0070950984954833984, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 695, \"connections\": 6}', '2025-07-08 01:19:03'),
(1972, 5, 0, 0.03671, NULL, NULL, '2025-07-08 01:19:03'),
(1973, 6, 1, 0.011131, NULL, NULL, '2025-07-08 01:19:03'),
(1974, 7, 0, 0.05340886116027832, '', NULL, '2025-07-08 01:19:03'),
(1975, 5, 0, 0.03157, NULL, NULL, '2025-07-08 01:19:06'),
(1976, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:13'),
(1977, 2, 1, 0.017300128936767578, NULL, NULL, '2025-07-08 01:19:13'),
(1978, 3, 1, 0.039530038833618164, NULL, '{\"version\": \"7.4.2\", \"uptime\": 87, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:13'),
(1979, 4, 1, 0.0190432071685791, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 705, \"connections\": 6}', '2025-07-08 01:19:13'),
(1980, 5, 0, 0.079781, NULL, NULL, '2025-07-08 01:19:13'),
(1981, 6, 1, 0.010823, NULL, NULL, '2025-07-08 01:19:13'),
(1982, 7, 0, 0.03655886650085449, '', NULL, '2025-07-08 01:19:13'),
(1983, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:16'),
(1984, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:21'),
(1985, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:23'),
(1986, 2, 1, 0.0024137496948242188, NULL, NULL, '2025-07-08 01:19:23'),
(1987, 3, 1, 0.011979818344116211, NULL, '{\"version\": \"7.4.2\", \"uptime\": 97, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:23'),
(1988, 4, 1, 0.006363868713378906, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 715, \"connections\": 6}', '2025-07-08 01:19:23'),
(1989, 5, 0, 0.007692, NULL, NULL, '2025-07-08 01:19:23'),
(1990, 6, 1, 0.009598, NULL, NULL, '2025-07-08 01:19:23'),
(1991, 7, 0, 0.02379298210144043, '', NULL, '2025-07-08 01:19:23'),
(1992, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:33'),
(1993, 2, 1, 0.0006489753723144531, NULL, NULL, '2025-07-08 01:19:33'),
(1994, 3, 1, 0.011042118072509766, NULL, '{\"version\": \"7.4.2\", \"uptime\": 107, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:33'),
(1995, 4, 1, 0.0048906803131103516, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 725, \"connections\": 6}', '2025-07-08 01:19:33'),
(1996, 5, 0, 0.011434, NULL, NULL, '2025-07-08 01:19:33'),
(1997, 6, 1, 0.041256, NULL, NULL, '2025-07-08 01:19:33'),
(1998, 7, 0, 0.11424374580383301, '', NULL, '2025-07-08 01:19:33'),
(1999, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:48'),
(2000, 2, 1, 0.0006351470947265625, NULL, NULL, '2025-07-08 01:19:48'),
(2001, 3, 1, 0.26962780952453613, NULL, '{\"version\": \"7.4.2\", \"uptime\": 122, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:48'),
(2002, 4, 1, 0.0059130191802978516, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 740, \"connections\": 6}', '2025-07-08 01:19:48'),
(2003, 5, 0, 0.005489, NULL, NULL, '2025-07-08 01:19:48'),
(2004, 6, 1, 0.005171, NULL, NULL, '2025-07-08 01:19:48'),
(2005, 7, 0, 0.019577741622924805, '', NULL, '2025-07-08 01:19:48'),
(2006, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:52'),
(2007, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:19:53'),
(2008, 2, 1, 0.00127410888671875, NULL, NULL, '2025-07-08 01:19:53'),
(2009, 3, 1, 0.04031109809875488, NULL, '{\"version\": \"7.4.2\", \"uptime\": 127, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:19:53'),
(2010, 4, 1, 0.008059263229370117, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 745, \"connections\": 6}', '2025-07-08 01:19:53'),
(2011, 5, 0, 0.189298, NULL, NULL, '2025-07-08 01:19:53'),
(2012, 6, 1, 0.090918, NULL, NULL, '2025-07-08 01:19:53'),
(2013, 7, 0, 0.02235698699951172, '', NULL, '2025-07-08 01:19:53'),
(2014, 1, 0, NULL, '(\'Connection aborted.\', ConnectionResetError(54, \'Connection reset by peer\'))', NULL, '2025-07-08 01:20:03'),
(2015, 2, 1, 0.0006051063537597656, NULL, NULL, '2025-07-08 01:20:03'),
(2016, 3, 1, 0.014070749282836914, NULL, '{\"version\": \"7.4.2\", \"uptime\": 137, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 01:20:03'),
(2017, 4, 1, 0.006186962127685547, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 755, \"connections\": 6}', '2025-07-08 01:20:03'),
(2018, 5, 0, 0.015868, NULL, NULL, '2025-07-08 01:20:03'),
(2019, 6, 1, 0.151241, NULL, NULL, '2025-07-08 01:20:03'),
(2020, 7, 0, 0.20889496803283691, '', NULL, '2025-07-08 01:20:03'),
(2021, 1, 1, 0.689295, NULL, NULL, '2025-07-08 02:24:25'),
(2022, 2, 1, 0.0016372203826904297, NULL, NULL, '2025-07-08 02:24:25'),
(2023, 3, 1, 0.03486204147338867, NULL, '{\"version\": \"7.4.2\", \"uptime\": 3999, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:24:25'),
(2024, 4, 1, 0.010039806365966797, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4617, \"connections\": 6}', '2025-07-08 02:24:25'),
(2025, 5, 0, 0.026166, NULL, NULL, '2025-07-08 02:24:25'),
(2026, 6, 1, 0.080663, NULL, NULL, '2025-07-08 02:24:25'),
(2027, 7, 0, 0.08640313148498535, '', NULL, '2025-07-08 02:24:25'),
(2028, 1, 1, 0.059565, NULL, NULL, '2025-07-08 02:24:34'),
(2029, 2, 1, 0.0023369789123535156, NULL, NULL, '2025-07-08 02:24:34'),
(2030, 3, 1, 0.02039790153503418, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4008, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:24:34'),
(2031, 4, 1, 0.3169558048248291, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4626, \"connections\": 6}', '2025-07-08 02:24:35'),
(2032, 5, 0, 0.019454, NULL, NULL, '2025-07-08 02:24:35'),
(2033, 6, 1, 0.01217, NULL, NULL, '2025-07-08 02:24:35'),
(2034, 7, 0, 0.03667306900024414, '', NULL, '2025-07-08 02:24:35'),
(2035, 1, 1, 0.045741, NULL, NULL, '2025-07-08 02:24:44'),
(2036, 2, 1, 0.0022001266479492188, NULL, NULL, '2025-07-08 02:24:44'),
(2037, 3, 1, 0.01564621925354004, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4018, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:24:44'),
(2038, 4, 1, 0.016913175582885742, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4636, \"connections\": 6}', '2025-07-08 02:24:44'),
(2039, 5, 0, 0.017914, NULL, NULL, '2025-07-08 02:24:44'),
(2040, 6, 1, 0.014479, NULL, NULL, '2025-07-08 02:24:44'),
(2041, 7, 0, 0.11070108413696289, '', NULL, '2025-07-08 02:24:45'),
(2042, 1, 1, 0.048873, NULL, NULL, '2025-07-08 02:24:54'),
(2043, 2, 1, 0.0019948482513427734, NULL, NULL, '2025-07-08 02:24:54'),
(2044, 3, 1, 0.013039112091064453, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4028, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:24:54'),
(2045, 4, 1, 0.008669853210449219, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4646, \"connections\": 6}', '2025-07-08 02:24:54'),
(2046, 5, 0, 0.006498, NULL, NULL, '2025-07-08 02:24:54'),
(2047, 6, 1, 0.045716, NULL, NULL, '2025-07-08 02:24:54'),
(2048, 7, 0, 0.09367012977600098, '', NULL, '2025-07-08 02:24:55'),
(2049, 1, 1, 0.067817, NULL, NULL, '2025-07-08 02:25:04'),
(2050, 2, 1, 0.012084007263183594, NULL, NULL, '2025-07-08 02:25:04'),
(2051, 3, 1, 0.012387990951538086, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4038, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:25:04'),
(2052, 4, 1, 0.013922929763793945, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4656, \"connections\": 6}', '2025-07-08 02:25:04'),
(2053, 5, 0, 0.015449, NULL, NULL, '2025-07-08 02:25:04'),
(2054, 6, 1, 0.052576, NULL, NULL, '2025-07-08 02:25:04'),
(2055, 7, 0, 0.04634904861450195, '', NULL, '2025-07-08 02:25:05'),
(2056, 1, 1, 0.090212, NULL, NULL, '2025-07-08 02:25:14'),
(2057, 2, 1, 0.0017511844635009766, NULL, NULL, '2025-07-08 02:25:14'),
(2058, 3, 1, 0.018833160400390625, NULL, '{\"version\": \"7.4.2\", \"uptime\": 4048, \"used_memory\": \"1.01M\", \"connected_clients\": 1}', '2025-07-08 02:25:14'),
(2059, 4, 1, 0.1728980541229248, NULL, '{\"version\": \"10.4.17-MariaDB\", \"uptime\": 4667, \"connections\": 6}', '2025-07-08 02:25:15'),
(2060, 5, 0, 0.025487, NULL, NULL, '2025-07-08 02:25:15'),
(2061, 6, 1, 0.024231, NULL, NULL, '2025-07-08 02:25:15'),
(2062, 7, 0, 0.20925116539001465, '', NULL, '2025-07-08 02:25:15');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `service_stats`
--

CREATE TABLE `service_stats` (
  `id` int(11) NOT NULL,
  `service_id` int(11) NOT NULL,
  `date` date NOT NULL,
  `total_checks` int(11) DEFAULT 0,
  `successful_checks` int(11) DEFAULT 0,
  `failed_checks` int(11) DEFAULT 0,
  `avg_response_time` double DEFAULT NULL,
  `min_response_time` double DEFAULT NULL,
  `max_response_time` double DEFAULT NULL,
  `total_downtime` int(11) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `service_stats`
--

INSERT INTO `service_stats` (`id`, `service_id`, `date`, `total_checks`, `successful_checks`, `failed_checks`, `avg_response_time`, `min_response_time`, `max_response_time`, `total_downtime`, `created_at`, `updated_at`) VALUES
(1, 6, '2025-07-07', 293, 206, 87, 0.008703878640776692, 0.003314, 0.151241, 0, '2025-07-07 15:21:16', '2025-07-08 02:25:15'),
(2, 4, '2025-07-07', 291, 291, 0, 0.009531160400495496, 0.0026090145111083984, 0.3801112174987793, 0, '2025-07-07 15:21:24', '2025-07-08 02:25:15'),
(3, 7, '2025-07-07', 288, 0, 288, NULL, NULL, NULL, 0, '2025-07-07 15:21:26', '2025-07-08 02:25:15'),
(4, 3, '2025-07-07', 288, 272, 16, 0.014522621736806976, 0.004825115203857422, 0.28368687629699707, 0, '2025-07-07 15:21:31', '2025-07-08 02:25:14'),
(5, 5, '2025-07-07', 291, 0, 291, NULL, NULL, NULL, 0, '2025-07-07 15:21:33', '2025-07-08 02:25:15'),
(6, 1, '2025-07-07', 291, 261, 30, 0.020268222222222222, 0.005797, 0.689295, 0, '2025-07-07 15:21:38', '2025-07-08 02:25:14'),
(7, 2, '2025-07-07', 292, 277, 15, 0.0015660115527762403, 0.00043392181396484375, 0.028510093688964844, 0, '2025-07-07 15:21:39', '2025-07-08 02:25:14');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `session_logs`
--

CREATE TABLE `session_logs` (
  `id` int(11) NOT NULL,
  `session_id` int(11) NOT NULL,
  `command` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `output` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `execution_time` float DEFAULT NULL,
  `exit_code` int(11) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `session_participants`
--

CREATE TABLE `session_participants` (
  `id` int(11) NOT NULL,
  `session_id` int(11) NOT NULL,
  `email` varchar(120) NOT NULL,
  `access_token` varchar(64) NOT NULL,
  `invitation_sent` tinyint(1) NOT NULL DEFAULT 0,
  `reminder_sent` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Participantes autorizados por sesión';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ssh_sessions`
--

CREATE TABLE `ssh_sessions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hostname` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` int(11) DEFAULT 22,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `auth_type` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT 'password',
  `password_encrypted` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `key_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `last_used_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 0,
  `connected_at` datetime DEFAULT NULL,
  `last_activity` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `ssh_sessions`
--

INSERT INTO `ssh_sessions` (`id`, `user_id`, `name`, `hostname`, `port`, `username`, `auth_type`, `password_encrypted`, `key_path`, `created_at`, `last_used_at`, `is_active`, `connected_at`, `last_activity`) VALUES
(1, 1, 'XPLAGIAX_SERVER', '74.208.44.179', 22, 'root', 'password', 'Z0FBQUFBQm9heGdmdDFRWFZrNDU1elVDa0t4dU5nVTF3eXpCckxYV0dXd0ptTi1mYmhvTFJwNVAtb0VHSF82ajh2U2w4VC1HSzh4bUVzODkwN2JveGJoeTNKaWoxYW1MVUE9PQ==', '', '2025-07-07 00:43:11', '2025-07-08 02:25:36', 1, '2025-07-08 02:25:36', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `storage_addons`
--

CREATE TABLE `storage_addons` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `storage_mb` int(11) NOT NULL,
  `price_monthly_usd` decimal(10,2) NOT NULL,
  `applicable_plan_id` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `storage_addons`
--

INSERT INTO `storage_addons` (`id`, `name`, `storage_mb`, `price_monthly_usd`, `applicable_plan_id`, `is_active`, `created_at`) VALUES
(1, 'Extra 10GB for Individual plan', 10240, '2.00', 2, 1, '2025-04-15 12:00:47'),
(2, 'Extra 10GB for Institutes plan', 10240, '3.00', 3, 1, '2025-04-15 12:00:47');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `storage_plans`
--

CREATE TABLE `storage_plans` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `base_storage_mb` int(11) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `storage_plans`
--

INSERT INTO `storage_plans` (`id`, `name`, `base_storage_mb`, `description`, `is_active`, `created_at`) VALUES
(1, 'Starter', 50, 'Free plan with 50 MB of storage', 1, '2025-04-15 12:00:47'),
(2, 'Individual', 5120, 'Individual plan with 5 GB of storage', 1, '2025-04-15 12:00:47'),
(3, 'Institutes', 51200, 'Plan for Institutes with 50 GB of storage', 1, '2025-04-15 12:00:47');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `student_submissions`
--

CREATE TABLE `student_submissions` (
  `id` int(11) NOT NULL,
  `session_id` int(11) NOT NULL,
  `student_id` int(11) DEFAULT NULL,
  `email` varchar(120) NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `file_size` int(11) NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `uploaded_at` datetime NOT NULL DEFAULT current_timestamp(),
  `last_modified` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `professor_comment` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Documentos entregados por estudiantes';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `submission_sessions`
--

CREATE TABLE `submission_sessions` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `professor_id` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `analysis_started` tinyint(1) NOT NULL DEFAULT 0,
  `analysis_completed` tinyint(1) NOT NULL DEFAULT 0,
  `forced_analysis` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sesiones de entrega creadas por profesores';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `_password_hash` varchar(255) DEFAULT NULL,
  `hashcode` varchar(255) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `lastname` varchar(100) DEFAULT NULL,
  `avatar` varchar(200) DEFAULT NULL,
  `tokens` text DEFAULT NULL,
  `institute` varchar(255) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `token` varchar(32) DEFAULT NULL,
  `active_session` tinyint(1) DEFAULT NULL,
  `confirmado` tinyint(1) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `storage_plan_id` int(11) DEFAULT NULL,
  `used_storage_bytes` bigint(20) DEFAULT 0,
  `user_type` enum('Starter','Individual','Institutes') DEFAULT 'Starter',
  `totp_secret` varchar(16) DEFAULT NULL,
  `is_professor` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`id`, `email`, `_password_hash`, `hashcode`, `name`, `lastname`, `avatar`, `tokens`, `institute`, `country`, `is_active`, `token`, `active_session`, `confirmado`, `user_id`, `created_date`, `storage_plan_id`, `used_storage_bytes`, `user_type`, `totp_secret`, `is_professor`) VALUES
(1, 'rubeneduardonova@gmail.com', '$2b$12$nmEH/jAI6U5WkGk68V4uMOZHmFits6pJlId.dLffAgCqPDvKu8EUq', '', 'ruben', 'Nova', '', NULL, '1', '1', 0, 'faa0d9c09258565d30a2a3552764ca8e', 1, 0, NULL, '2024-02-22 20:04:43', 1, 6161451, 'Starter', NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users_admin`
--

CREATE TABLE `users_admin` (
  `id` int(11) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT 'user',
  `created_at` datetime DEFAULT current_timestamp(),
  `last_login_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `users_admin`
--

INSERT INTO `users_admin` (`id`, `username`, `email`, `password_hash`, `role`, `created_at`, `last_login_at`, `is_active`) VALUES
(1, 'Ruben Eduardo Gonzalez Nova', 'rgonzalez@uryxtech.com', 'scrypt:32768:8:1$LRKm5jfeqr1Btd8v$0b42e1325ded661e83ffc1ee9eb3b05e9c82c822ed8a15071752e6fa10bb6aaed52726e211e2a4edad75b11d2a89c3f50937141a70366dc55059bdd009c5d53d', 'admin', '2025-07-04 17:42:06', '2025-07-08 16:41:14', 1),
(2, 'David Mendez', 'dmendez@uryxtech.com', 'scrypt:32768:8:1$q2GtrXiYJ6BjhDWH$d2e4b89e289ffb6ef4c923b9d61da77988b15d7d342380774367c8c166eb68c1b95d3652b6073ef5659d182953d0a102ee28ec4cde515188e96223ec2890b619', 'admin', '2025-07-04 18:05:02', NULL, 0),
(3, 'Luis Aquino', 'laquino@uryxtech.com', 'scrypt:32768:8:1$K8jUkOUTKKoOk84R$3d38fdf5a26a4fc0e134094ea27cac1dc43c8eaf4cc25988eef04f43ab752f936f4c610e895856720ef12a654ac3ee2455e2c8dd57be656ed8df6d22ee436307', 'manager', '2025-07-04 18:07:26', NULL, 1),
(4, 'Pavel Santos', 'psantos@uryxtech.com', 'scrypt:32768:8:1$82s3pAnRIavWXzdV$a18286b77bf905b58071f6bbbbd249f81ec93ff23004be0955f5d943eda91f1220860af25c6e2a243b841e6d0dcbc16d1f5745a9387f0a2bf39a9cc35403d460', 'manager', '2025-07-04 18:08:39', NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users_log`
--

CREATE TABLE `users_log` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `log_status_ID` int(11) DEFAULT NULL,
  `created_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `user_addon_subscriptions`
--

CREATE TABLE `user_addon_subscriptions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `addon_id` int(11) NOT NULL,
  `start_date` datetime DEFAULT current_timestamp(),
  `expiry_date` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `auto_renew` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura para la vista `analysis_stats`
--
DROP TABLE IF EXISTS `analysis_stats`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `analysis_stats`  AS SELECT `da`.`id` AS `id`, `da`.`analysis_id` AS `analysis_id`, `da`.`title` AS `title`, `da`.`user_id` AS `user_id`, `da`.`analysis_date` AS `analysis_date`, `da`.`pages` AS `pages`, `da`.`language` AS `language`, count(`cp`.`id`) AS `total_paragraphs_counted`, sum(case when `cp`.`is_human` = 1 then 1 else 0 end) AS `human_paragraphs`, sum(case when `cp`.`is_human` = 0 then 1 else 0 end) AS `ai_paragraphs`, avg(`cp`.`final_confidence`) AS `avg_confidence`, min(`cp`.`final_confidence`) AS `min_confidence`, max(`cp`.`final_confidence`) AS `max_confidence` FROM (`document_analyses` `da` left join `classified_paragraphs` `cp` on(`da`.`analysis_id` = `cp`.`analysis_id`)) GROUP BY `da`.`id`, `da`.`analysis_id`, `da`.`title`, `da`.`user_id`, `da`.`analysis_date`, `da`.`pages`, `da`.`language` ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_log_user` (`user_id`),
  ADD KEY `idx_log_action` (`action`),
  ADD KEY `idx_log_entity` (`entity_type`,`entity_id`),
  ADD KEY `idx_log_timestamp` (`timestamp`);

--
-- Indices de la tabla `City`
--
ALTER TABLE `City`
  ADD PRIMARY KEY (`id`),
  ADD KEY `state_id` (`state_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `classified_paragraphs`
--
ALTER TABLE `classified_paragraphs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_analysis_id` (`analysis_id`),
  ADD KEY `idx_page_paragraph` (`page_number`,`paragraph_number`),
  ADD KEY `idx_is_human` (`is_human`),
  ADD KEY `idx_confidence` (`final_confidence`),
  ADD KEY `idx_predicted_model` (`predicted_model`),
  ADD KEY `idx_human_probability` (`human_probability`),
  ADD KEY `idx_ai_probability` (`ai_probability`),
  ADD KEY `idx_page_number` (`page_number`);

--
-- Indices de la tabla `contact_interactions`
--
ALTER TABLE `contact_interactions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `contact_id` (`contact_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `contact_sales`
--
ALTER TABLE `contact_sales`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `contact_id` (`contact_id`),
  ADD KEY `fk_assigned_user` (`assigned_to`);

--
-- Indices de la tabla `container_status`
--
ALTER TABLE `container_status`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_container_id` (`container_id`),
  ADD KEY `idx_timestamp` (`timestamp`),
  ADD KEY `idx_running` (`running`);

--
-- Indices de la tabla `Country`
--
ALTER TABLE `Country`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Docmodels`
--
ALTER TABLE `Docmodels`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `Doctype`
--
ALTER TABLE `Doctype`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Documents`
--
ALTER TABLE `Documents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `doctype_id` (`doctype_id`),
  ADD KEY `country_id` (`country_id`),
  ADD KEY `institution_id` (`institution_id`),
  ADD KEY `lenguage_id` (`lenguage_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `document_analyses`
--
ALTER TABLE `document_analyses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `analysis_id` (`analysis_id`),
  ADD KEY `idx_analysis_id` (`analysis_id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_analysis_date` (`analysis_date`),
  ADD KEY `idx_success` (`success`);

--
-- Indices de la tabla `document_versions`
--
ALTER TABLE `document_versions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_version_submission` (`submission_id`),
  ADD KEY `idx_version_date` (`uploaded_at`);

--
-- Indices de la tabla `ErrorLogAdmin`
--
ALTER TABLE `ErrorLogAdmin`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `ErrorLogUsers`
--
ALTER TABLE `ErrorLogUsers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `files`
--
ALTER TABLE `files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_file_folder` (`folder_id`),
  ADD KEY `fk_file_user` (`user_id`);

--
-- Indices de la tabla `file_transfers`
--
ALTER TABLE `file_transfers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_session_id` (`session_id`),
  ADD KEY `idx_transfer_type` (`transfer_type`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_started_at` (`started_at`);

--
-- Indices de la tabla `folders`
--
ALTER TABLE `folders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_folder_parent` (`parent_id`),
  ADD KEY `fk_folder_user` (`user_id`);

--
-- Indices de la tabla `History_ai_analysis`
--
ALTER TABLE `History_ai_analysis`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `History_db_analysis`
--
ALTER TABLE `History_db_analysis`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Institution`
--
ALTER TABLE `Institution`
  ADD PRIMARY KEY (`id`),
  ADD KEY `institution_type` (`institution_type`),
  ADD KEY `city_id` (`city_id`),
  ADD KEY `country_id` (`country_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Institution_type`
--
ALTER TABLE `Institution_type`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Lenguage`
--
ALTER TABLE `Lenguage`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `log_status`
--
ALTER TABLE `log_status`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `Patents`
--
ALTER TABLE `Patents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `Province_state`
--
ALTER TABLE `Province_state`
  ADD PRIMARY KEY (`id`),
  ADD KEY `country_id` (`country_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indices de la tabla `services`
--
ALTER TABLE `services`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `idx_service_active_monitored` (`is_active`,`is_monitored`),
  ADD KEY `idx_service_type` (`service_type`),
  ADD KEY `idx_service_host_port` (`host`,`port`);

--
-- Indices de la tabla `service_logs`
--
ALTER TABLE `service_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_service_log_service_time` (`service_id`,`checked_at`),
  ADD KEY `idx_service_log_status_time` (`status`,`checked_at`);

--
-- Indices de la tabla `service_stats`
--
ALTER TABLE `service_stats`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `service_id` (`service_id`,`date`),
  ADD KEY `idx_service_stats_date` (`date`);

--
-- Indices de la tabla `session_logs`
--
ALTER TABLE `session_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_session_id` (`session_id`),
  ADD KEY `idx_timestamp` (`timestamp`),
  ADD KEY `idx_exit_code` (`exit_code`);

--
-- Indices de la tabla `session_participants`
--
ALTER TABLE `session_participants`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `access_token` (`access_token`),
  ADD UNIQUE KEY `unique_participant_per_session` (`session_id`,`email`),
  ADD KEY `idx_participant_token` (`access_token`),
  ADD KEY `idx_participant_email` (`email`),
  ADD KEY `idx_pending_submissions` (`session_id`,`email`,`invitation_sent`);

--
-- Indices de la tabla `ssh_sessions`
--
ALTER TABLE `ssh_sessions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_hostname` (`hostname`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_created_at` (`created_at`);

--
-- Indices de la tabla `storage_addons`
--
ALTER TABLE `storage_addons`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_addon_plan` (`applicable_plan_id`);

--
-- Indices de la tabla `storage_plans`
--
ALTER TABLE `storage_plans`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indices de la tabla `student_submissions`
--
ALTER TABLE `student_submissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_submission_per_session_email` (`session_id`,`email`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `idx_submission_email` (`email`),
  ADD KEY `idx_submission_date` (`uploaded_at`);

--
-- Indices de la tabla `submission_sessions`
--
ALTER TABLE `submission_sessions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_session_dates` (`start_date`,`end_date`),
  ADD KEY `idx_session_professor` (`professor_id`),
  ADD KEY `idx_session_status` (`analysis_started`,`analysis_completed`),
  ADD KEY `idx_active_sessions` (`professor_id`,`start_date`,`end_date`),
  ADD KEY `idx_session_name` (`name`(20));

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `fk_user_storage_plan` (`storage_plan_id`),
  ADD KEY `idx_user_email` (`email`),
  ADD KEY `idx_user_role` (`is_professor`);

--
-- Indices de la tabla `users_admin`
--
ALTER TABLE `users_admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_user_active_role` (`is_active`,`role`),
  ADD KEY `idx_user_created` (`created_at`),
  ADD KEY `idx_users_username` (`username`),
  ADD KEY `idx_users_email` (`email`),
  ADD KEY `idx_users_role` (`role`),
  ADD KEY `idx_users_is_active` (`is_active`);

--
-- Indices de la tabla `users_log`
--
ALTER TABLE `users_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `log_status_ID` (`log_status_ID`);

--
-- Indices de la tabla `user_addon_subscriptions`
--
ALTER TABLE `user_addon_subscriptions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_subscription_user` (`user_id`),
  ADD KEY `fk_subscription_addon` (`addon_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `City`
--
ALTER TABLE `City`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=67;

--
-- AUTO_INCREMENT de la tabla `classified_paragraphs`
--
ALTER TABLE `classified_paragraphs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=973;

--
-- AUTO_INCREMENT de la tabla `contact_interactions`
--
ALTER TABLE `contact_interactions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `contact_sales`
--
ALTER TABLE `contact_sales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `container_status`
--
ALTER TABLE `container_status`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `Country`
--
ALTER TABLE `Country`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `Docmodels`
--
ALTER TABLE `Docmodels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `Doctype`
--
ALTER TABLE `Doctype`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT de la tabla `Documents`
--
ALTER TABLE `Documents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `document_analyses`
--
ALTER TABLE `document_analyses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT de la tabla `document_versions`
--
ALTER TABLE `document_versions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ErrorLogAdmin`
--
ALTER TABLE `ErrorLogAdmin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ErrorLogUsers`
--
ALTER TABLE `ErrorLogUsers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `files`
--
ALTER TABLE `files`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `file_transfers`
--
ALTER TABLE `file_transfers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `folders`
--
ALTER TABLE `folders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `History_ai_analysis`
--
ALTER TABLE `History_ai_analysis`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `History_db_analysis`
--
ALTER TABLE `History_db_analysis`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `Institution`
--
ALTER TABLE `Institution`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=96;

--
-- AUTO_INCREMENT de la tabla `Institution_type`
--
ALTER TABLE `Institution_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `Lenguage`
--
ALTER TABLE `Lenguage`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `log_status`
--
ALTER TABLE `log_status`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `Patents`
--
ALTER TABLE `Patents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `Province_state`
--
ALTER TABLE `Province_state`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `services`
--
ALTER TABLE `services`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `service_logs`
--
ALTER TABLE `service_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2084;

--
-- AUTO_INCREMENT de la tabla `service_stats`
--
ALTER TABLE `service_stats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `session_logs`
--
ALTER TABLE `session_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `session_participants`
--
ALTER TABLE `session_participants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ssh_sessions`
--
ALTER TABLE `ssh_sessions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `storage_addons`
--
ALTER TABLE `storage_addons`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `storage_plans`
--
ALTER TABLE `storage_plans`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `student_submissions`
--
ALTER TABLE `student_submissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `submission_sessions`
--
ALTER TABLE `submission_sessions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `users_admin`
--
ALTER TABLE `users_admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `users_log`
--
ALTER TABLE `users_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `user_addon_subscriptions`
--
ALTER TABLE `user_addon_subscriptions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `City`
--
ALTER TABLE `City`
  ADD CONSTRAINT `city_ibfk_1` FOREIGN KEY (`state_id`) REFERENCES `Province_state` (`id`),
  ADD CONSTRAINT `city_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `classified_paragraphs`
--
ALTER TABLE `classified_paragraphs`
  ADD CONSTRAINT `classified_paragraphs_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `document_analyses` (`analysis_id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `contact_interactions`
--
ALTER TABLE `contact_interactions`
  ADD CONSTRAINT `contact_interactions_ibfk_1` FOREIGN KEY (`contact_id`) REFERENCES `contact_sales` (`contact_id`),
  ADD CONSTRAINT `contact_interactions_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `contact_sales`
--
ALTER TABLE `contact_sales`
  ADD CONSTRAINT `fk_assigned_user` FOREIGN KEY (`assigned_to`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Country`
--
ALTER TABLE `Country`
  ADD CONSTRAINT `country_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Doctype`
--
ALTER TABLE `Doctype`
  ADD CONSTRAINT `doctype_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Documents`
--
ALTER TABLE `Documents`
  ADD CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`doctype_id`) REFERENCES `Doctype` (`id`),
  ADD CONSTRAINT `documents_ibfk_2` FOREIGN KEY (`country_id`) REFERENCES `Country` (`id`),
  ADD CONSTRAINT `documents_ibfk_3` FOREIGN KEY (`institution_id`) REFERENCES `Institution` (`id`),
  ADD CONSTRAINT `documents_ibfk_4` FOREIGN KEY (`lenguage_id`) REFERENCES `Lenguage` (`id`),
  ADD CONSTRAINT `documents_ibfk_5` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Filtros para la tabla `document_versions`
--
ALTER TABLE `document_versions`
  ADD CONSTRAINT `document_versions_ibfk_1` FOREIGN KEY (`submission_id`) REFERENCES `student_submissions` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ErrorLogAdmin`
--
ALTER TABLE `ErrorLogAdmin`
  ADD CONSTRAINT `errorlogadmin_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `ErrorLogUsers`
--
ALTER TABLE `ErrorLogUsers`
  ADD CONSTRAINT `errorlogusers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Filtros para la tabla `files`
--
ALTER TABLE `files`
  ADD CONSTRAINT `fk_file_folder` FOREIGN KEY (`folder_id`) REFERENCES `folders` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_file_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `file_transfers`
--
ALTER TABLE `file_transfers`
  ADD CONSTRAINT `file_transfers_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `ssh_sessions` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `folders`
--
ALTER TABLE `folders`
  ADD CONSTRAINT `fk_folder_parent` FOREIGN KEY (`parent_id`) REFERENCES `folders` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_folder_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `History_ai_analysis`
--
ALTER TABLE `History_ai_analysis`
  ADD CONSTRAINT `history_ai_analysis_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Filtros para la tabla `History_db_analysis`
--
ALTER TABLE `History_db_analysis`
  ADD CONSTRAINT `history_db_analysis_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Filtros para la tabla `Institution`
--
ALTER TABLE `Institution`
  ADD CONSTRAINT `institution_ibfk_1` FOREIGN KEY (`institution_type`) REFERENCES `Institution_type` (`id`),
  ADD CONSTRAINT `institution_ibfk_2` FOREIGN KEY (`city_id`) REFERENCES `City` (`id`),
  ADD CONSTRAINT `institution_ibfk_3` FOREIGN KEY (`country_id`) REFERENCES `Country` (`id`),
  ADD CONSTRAINT `institution_ibfk_4` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Institution_type`
--
ALTER TABLE `Institution_type`
  ADD CONSTRAINT `institution_type_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Lenguage`
--
ALTER TABLE `Lenguage`
  ADD CONSTRAINT `lenguage_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Patents`
--
ALTER TABLE `Patents`
  ADD CONSTRAINT `patents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `Province_state`
--
ALTER TABLE `Province_state`
  ADD CONSTRAINT `province_state_ibfk_1` FOREIGN KEY (`country_id`) REFERENCES `Country` (`id`),
  ADD CONSTRAINT `province_state_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `services`
--
ALTER TABLE `services`
  ADD CONSTRAINT `services_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

--
-- Filtros para la tabla `service_logs`
--
ALTER TABLE `service_logs`
  ADD CONSTRAINT `service_logs_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `service_stats`
--
ALTER TABLE `service_stats`
  ADD CONSTRAINT `service_stats_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `services` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `session_logs`
--
ALTER TABLE `session_logs`
  ADD CONSTRAINT `session_logs_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `ssh_sessions` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `session_participants`
--
ALTER TABLE `session_participants`
  ADD CONSTRAINT `session_participants_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `submission_sessions` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ssh_sessions`
--
ALTER TABLE `ssh_sessions`
  ADD CONSTRAINT `ssh_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `storage_addons`
--
ALTER TABLE `storage_addons`
  ADD CONSTRAINT `fk_addon_plan` FOREIGN KEY (`applicable_plan_id`) REFERENCES `storage_plans` (`id`);

--
-- Filtros para la tabla `student_submissions`
--
ALTER TABLE `student_submissions`
  ADD CONSTRAINT `student_submissions_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `submission_sessions` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `student_submissions_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `submission_sessions`
--
ALTER TABLE `submission_sessions`
  ADD CONSTRAINT `submission_sessions_ibfk_1` FOREIGN KEY (`professor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_user_storage_plan` FOREIGN KEY (`storage_plan_id`) REFERENCES `storage_plans` (`id`),
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users_admin` (`id`);

--
-- Filtros para la tabla `users_log`
--
ALTER TABLE `users_log`
  ADD CONSTRAINT `users_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `users_log_ibfk_2` FOREIGN KEY (`log_status_ID`) REFERENCES `log_status` (`id`);

--
-- Filtros para la tabla `user_addon_subscriptions`
--
ALTER TABLE `user_addon_subscriptions`
  ADD CONSTRAINT `fk_subscription_addon` FOREIGN KEY (`addon_id`) REFERENCES `storage_addons` (`id`),
  ADD CONSTRAINT `fk_subscription_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
