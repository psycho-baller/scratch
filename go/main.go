package main

import (
	"fmt"
	"math"
	"sort"
)

type Point struct {
	X float64
	Y float64
}

func (p Point) DistanceFrom(q Point) float64 {
	dx := p.X - q.X
	dy := p.Y - q.Y

	return math.Sqrt((dx * dx) + (dy * dy))
}

func bruteForceClosestPair(points []Point) (Point, Point, float64) {
	n := len(points)
	minDist := math.Inf(1)
	i := -1
	j := -1

	// O(n^2) time to search through all pairs
	for k := 0; k < n; k += 1 {
		for l := k + 1; l < n; l += 1 {
			if dist := points[k].DistanceFrom(points[l]); dist < minDist {
				minDist = dist
				i = k
				j = l
			}
		}
	}

	return points[i], points[j], minDist
}

func closestInPrunedStrip(prunedStrip []Point) (Point, Point, float64) {
	n := len(prunedStrip)
	minDist := math.Inf(1)
	i := -1
	j := -1

	// Outer loop runs O(n) times
	for k := 0; k < n; k += 1 {
		start := k + 1
		end := min(k+7, n) // Clamp the end index to ensure we do not overflow

		// Inner loop runs at most 6 times so it can be considered O(1)
		// This is due to the geometrical constraints of the problem
		// Since we are looping from points sorted by Y value in descending order,
		// We only need to check 6 points ahead of the current

		// From the current point, draw a line to the left and right `minDist` length
		// From the current point draw a line down `minDist` length
		// This creates a (2 * `minDist`^2) area shape like so:
		//
		// +---<minDist>-----[Point k]-----<minDist>---+
		// |				   	 |				 	   |
		// |			 	  <minDist>			 	   |
		// |				   	 |				 	   |
		// +---<minDist>---------+---------<minDist>---+
		//
		// At each '+' symbol, a point could exist, in the worst case, this is 6
		//
		// Assume that `minDist` is the smallest distance between 2 points on the plane
		// Then every point at the '+' signs must be exactly `minDist` away from point `k`
		// However, if a point is found with distance (`currDist`) less than `minDist`,
		// a contradiction is obtained implying that `minDist` is not the shortest
		// and a distance across the border shorter than `minDist` does exist.
		for l := start; l < end; l += 1 {
			if currDist := prunedStrip[k].DistanceFrom(prunedStrip[l]); currDist < minDist {
				minDist = currDist
				i = k
				j = l
			}
		}
	}

	return prunedStrip[i], prunedStrip[j], minDist
}

func closestPointsRec(xSorted []Point, ySorted []Point) (Point, Point) {
	n := len(xSorted)

	// Base case
	// This can be considered O(1) as the input size is at most 3
	if n <= 3 {
		p1, p2, _ := bruteForceClosestPair(xSorted)
		return p1, p2
	}

	// Mark the vertical line that divides the points into two halves
	mid := n / 2
	midPoint := xSorted[mid]

	// Divide into left and half slices
	// This is O(1) as pointer tracking built-into go with slices
	left := xSorted[0:mid]
	right := xSorted[mid:n]

	// Conquer
	p1, q1 := closestPointsRec(left, ySorted)  // Closest pair in left half
	p2, q2 := closestPointsRec(right, ySorted) // Closest pair in right half

	// Calculate distances of the 2 closest points in the left and right halves
	distLeft := p1.DistanceFrom(q1)
	distRight := p2.DistanceFrom(q2)

	// Minimum distance between the two halves
	minDist := min(distLeft, distRight)

	// This will be a strip of width 2 * `minDist`
	// Spans delta distance from the `midPoint` in left and right directions
	// In class, I believe this was mentioned to be implemented as a linked list
	// but here, I just use a slice to keep it simple
	prunedStrip := make([]Point, 0, n)

	// Filter points that are further (horizontally) from the border than the current best distance
	// This is because a closer pair that exists across the border must have a distance less than `minDist`
	// O(n) time to search through the sorted Y array
	for _, p := range ySorted {
		if math.Abs(p.X-midPoint.X) < minDist {
			prunedStrip = append(prunedStrip, p)
		}
	}

	// Merge the two closest points from the left and right halves
	p3, q3, prunedMinDist := closestInPrunedStrip(prunedStrip)

	if prunedMinDist < minDist {
		// There exists a closer pair across the border
		return p3, q3
	} else if distLeft < distRight {
		// The closest pair is in the left half
		return p1, q1
	} else {
		// The closest pair is in the right half
		return p2, q2
	}
}

func ClosestPoints(points []Point) (Point, Point) {
	n := len(points)

	// Initialize sorted point arrays
	xSorted := make([]Point, n)
	ySorted := make([]Point, n)

	_ = copy(xSorted, points)
	_ = copy(ySorted, points)

	// Pre-sort points according to X and Y values
	// Descending order for X values
	// Should be O(n log n) time
	sort.Slice(xSorted, func(i int, j int) bool {
		return xSorted[i].X < xSorted[j].X
	})

	// Descending order for Y values
	// Should be O(n log n) time
	sort.Slice(ySorted, func(i int, j int) bool {
		return ySorted[i].Y < ySorted[j].Y
	})

	// Start recursion
	return closestPointsRec(xSorted, ySorted)
}

func main() {
	points := []Point{
		{X: 32, Y: 4},
		{X: 7, Y: 4},
		{X: 6, Y: 9},
		{X: 2, Y: 96},
	}

	p1, p2 := ClosestPoints(points)

	fmt.Printf("P1: %v, P2: %v\n", p1, p2)
}
