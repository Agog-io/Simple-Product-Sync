-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Εξυπηρετητής: localhost:3306
-- Χρόνος δημιουργίας: 25 Αυγ 2023 στις 17:43:14
-- Έκδοση διακομιστή: 5.5.68-MariaDB
-- Έκδοση PHP: 8.2.8

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Βάση δεδομένων: `extern_prods_db`
--

-- --------------------------------------------------------

--
-- Δομή πίνακα για τον πίνακα `extern_cats`
--

CREATE TABLE `extern_cats` (
  `id` int(11) NOT NULL,
  `source` longtext NOT NULL,
  `fullpath` longtext NOT NULL,
  `name` longtext NOT NULL,
  `parent_id` int(11) NOT NULL,
  `url` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Δομή πίνακα για τον πίνακα `extern_images`
--

CREATE TABLE `extern_images` (
  `id` int(11) NOT NULL,
  `imageurl` longtext NOT NULL,
  `imagename` longtext NOT NULL,
  `serverpath` longtext NOT NULL,
  `sourceid` int(11) NOT NULL,
  `prodid` int(11) NOT NULL,
  `found` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Δομή πίνακα για τον πίνακα `extern_products`
--

CREATE TABLE `extern_products` (
  `id` int(11) NOT NULL,
  `name` longtext NOT NULL,
  `source` longtext NOT NULL,
  `url` longtext NOT NULL,
  `manufacturer` longtext NOT NULL,
  `sku_manuf` longtext NOT NULL,
  `id_supplier` longtext NOT NULL,
  `stock` int(11) NOT NULL,
  `availability` longtext NOT NULL,
  `price` double NOT NULL,
  `sale` double NOT NULL,
  `desc` longtext NOT NULL,
  `images` longtext NOT NULL,
  `found` int(11) NOT NULL,
  `parsed` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Δομή πίνακα για τον πίνακα `extern_relations`
--

CREATE TABLE `extern_relations` (
  `id` int(11) NOT NULL,
  `meta_key` longtext NOT NULL,
  `meta_value` longtext NOT NULL,
  `prod_id` int(11) NOT NULL,
  `source` longtext NOT NULL,
  `found` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Δομή πίνακα για τον πίνακα `extern_sources`
--

CREATE TABLE `extern_sources` (
  `id` int(11) NOT NULL,
  `source` longtext NOT NULL,
  `state` int(11) NOT NULL COMMENT '1 = ok\r\n2 = updating'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Ευρετήρια για άχρηστους πίνακες
--

--
-- Ευρετήρια για πίνακα `extern_cats`
--
ALTER TABLE `extern_cats`
  ADD PRIMARY KEY (`id`);

--
-- Ευρετήρια για πίνακα `extern_images`
--
ALTER TABLE `extern_images`
  ADD PRIMARY KEY (`id`);

--
-- Ευρετήρια για πίνακα `extern_products`
--
ALTER TABLE `extern_products`
  ADD PRIMARY KEY (`id`);

--
-- Ευρετήρια για πίνακα `extern_relations`
--
ALTER TABLE `extern_relations`
  ADD PRIMARY KEY (`id`);

--
-- Ευρετήρια για πίνακα `extern_sources`
--
ALTER TABLE `extern_sources`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT για άχρηστους πίνακες
--

--
-- AUTO_INCREMENT για πίνακα `extern_cats`
--
ALTER TABLE `extern_cats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT για πίνακα `extern_images`
--
ALTER TABLE `extern_images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT για πίνακα `extern_products`
--
ALTER TABLE `extern_products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT για πίνακα `extern_relations`
--
ALTER TABLE `extern_relations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT για πίνακα `extern_sources`
--
ALTER TABLE `extern_sources`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
